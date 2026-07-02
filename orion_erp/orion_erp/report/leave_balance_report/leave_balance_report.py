import frappe
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 140},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
        {"label": "Leave Type", "fieldname": "leave_type", "fieldtype": "Link", "options": "Leave Type", "width": 150},
        {"label": "Opening Balance", "fieldname": "opening_balance", "fieldtype": "Float", "width": 130},
        {"label": "Accrued", "fieldname": "accrued", "fieldtype": "Float", "width": 100},
        {"label": "Carry-Over", "fieldname": "carry_over", "fieldtype": "Float", "width": 100},
        {"label": "Taken", "fieldname": "taken", "fieldtype": "Float", "width": 90},
        {"label": "Encashed", "fieldname": "encashed", "fieldtype": "Float", "width": 100},
        {"label": "Current Balance", "fieldname": "current_balance", "fieldtype": "Float", "width": 130},
    ]


def _build_emp_query(filters):
    conds = ["emp.status = 'Active'"]
    vals = {}
    for field, col in [("employee", "emp.name"), ("department", "emp.department"), ("employee_category", "emp.custom_employee_category")]:
        if filters.get(field):
            conds.append(f"{col} = %({field})s")
            vals[field] = filters[field]
    return " AND ".join(conds), vals


def get_data(filters):
    filters = filters or {}
    emp_cond, emp_vals = _build_emp_query(filters)

    lt_cond = ""
    lt_vals = {}
    if filters.get("leave_type"):
        lt_cond = " AND lle.leave_type = %(leave_type)s"
        lt_vals["leave_type"] = filters["leave_type"]

    query = f"""
    WITH active_emp AS (
        SELECT name FROM `tabEmployee` emp WHERE {emp_cond}
    ),
    alloc AS (
        SELECT
            lle.employee,
            lle.leave_type,
            lle.leaves,
            lle.is_carry_forward,
            ROW_NUMBER() OVER (
                PARTITION BY lle.employee, lle.leave_type, lle.transaction_name
                ORDER BY lle.creation
            ) AS rn
        FROM `tabLeave Ledger Entry` lle
        INNER JOIN `tabLeave Allocation` la
            ON la.name = lle.transaction_name
            AND lle.transaction_type = 'Leave Allocation'
        WHERE lle.docstatus = 1
            AND lle.is_expired = 0
            AND la.expired = 0
            AND lle.employee IN (SELECT name FROM active_emp)
            {lt_cond}
    ),
    apps AS (
        SELECT employee, leave_type, SUM(ABS(leaves)) AS taken
        FROM `tabLeave Ledger Entry`
        WHERE docstatus = 1
            AND transaction_type = 'Leave Application'
            AND is_expired = 0
            AND employee IN (SELECT name FROM active_emp)
            {lt_cond.replace('lle.', '')}
        GROUP BY employee, leave_type
    ),
    enc AS (
        SELECT employee, leave_type, SUM(ABS(leaves)) AS encashed
        FROM `tabLeave Ledger Entry`
        WHERE docstatus = 1
            AND transaction_type = 'Leave Encashment'
            AND is_expired = 0
            AND employee IN (SELECT name FROM active_emp)
            {lt_cond.replace('lle.', '')}
        GROUP BY employee, leave_type
    )
    SELECT
        ae.employee,
        ae.leave_type,
        SUM(CASE WHEN ae.is_carry_forward = 0 AND ae.rn = 1 THEN ae.leaves ELSE 0 END) AS opening_balance,
        SUM(CASE WHEN ae.is_carry_forward = 0 AND ae.rn > 1 THEN ae.leaves ELSE 0 END) AS accrued,
        SUM(CASE WHEN ae.is_carry_forward = 1 THEN ae.leaves ELSE 0 END) AS carry_over,
        COALESCE(ap.taken, 0) AS taken,
        COALESCE(enc.encashed, 0) AS encashed
    FROM alloc ae
    LEFT JOIN apps ap ON ap.employee = ae.employee AND ap.leave_type = ae.leave_type
    LEFT JOIN enc ON enc.employee = ae.employee AND enc.leave_type = ae.leave_type
    GROUP BY ae.employee, ae.leave_type
    ORDER BY ae.employee, ae.leave_type
    """

    all_vals = {**emp_vals, **lt_vals}
    rows = frappe.db.sql(query, all_vals, as_dict=1)
    if not rows:
        return []

    emps = frappe.db.sql(
        "SELECT name, employee_name, department FROM `tabEmployee` WHERE status = 'Active'",
        as_dict=1,
    )
    name_map = {r.name: r for r in emps}

    result = []
    for r in rows:
        opening = flt(r.opening_balance)
        accrued = flt(r.accrued)
        carry_over = flt(r.carry_over)
        taken = flt(r.taken)
        encashed = flt(r.encashed)
        current = opening + accrued + carry_over - taken - encashed

        if not current and not opening and not accrued and not carry_over and not taken and not encashed:
            continue

        emp = name_map.get(r.employee, {})
        result.append({
            "employee": r.employee,
            "employee_name": emp.get("employee_name", ""),
            "department": emp.get("department", ""),
            "leave_type": r.leave_type,
            "opening_balance": opening,
            "accrued": accrued,
            "carry_over": carry_over,
            "taken": taken,
            "encashed": encashed,
            "current_balance": current,
        })

    return result
