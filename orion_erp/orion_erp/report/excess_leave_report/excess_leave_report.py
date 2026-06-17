import frappe
from frappe.utils import getdate, flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
        {"label": "Leave Type", "fieldname": "leave_type", "fieldtype": "Link", "options": "Leave Type", "width": 130},
        {"label": "Allocation", "fieldname": "allocation", "fieldtype": "Link", "options": "Leave Allocation", "width": 150},
        {"label": "Current Balance", "fieldname": "current_balance", "fieldtype": "Float", "width": 120},
        {"label": "Carry Over Limit", "fieldname": "carry_over_limit", "fieldtype": "Float", "width": 120},
        {"label": "Excess Days", "fieldname": "excess_days", "fieldtype": "Float", "width": 110},
        {"label": "Action Status", "fieldname": "action_status", "fieldtype": "Data", "width": 130},
        {"label": "Carry Forward Days", "fieldname": "carry_forward_days", "fieldtype": "Float", "width": 130},
        {"label": "Lapsed Days", "fieldname": "lapsed_days", "fieldtype": "Float", "width": 110},
        {"label": "Decision Date", "fieldname": "decision_date", "fieldtype": "Date", "width": 110},
        {"label": "Decided By", "fieldname": "decided_by", "fieldtype": "Link", "options": "User", "width": 120},
    ]


def get_data(filters):
    # Find all leave types that have a carry-forward limit
    leave_types_with_carry = frappe.db.sql_list("""
        SELECT name FROM `tabLeave Type`
        WHERE COALESCE(maximum_carry_forwarded_leaves, 0) > 0
    """)

    if not leave_types_with_carry:
        return []

    conditions = """
        WHERE la.docstatus = 1
        AND la.leave_type IN %(leave_types)s
        AND emp.status = 'Active'
    """
    values = {"leave_types": leave_types_with_carry}

    if filters.get("leave_type"):
        conditions += " AND la.leave_type = %(leave_type)s "
        values["leave_type"] = filters.get("leave_type")

    if filters.get("employee"):
        conditions += " AND la.employee = %(employee)s "
        values["employee"] = filters.get("employee")

    if filters.get("department"):
        conditions += " AND emp.department = %(department)s "
        values["department"] = filters.get("department")

    if filters.get("action_status"):
        if filters.get("action_status") == "Pending":
            conditions += " AND (la.custom_excess_leave_status IS NULL OR la.custom_excess_leave_status = 'Pending') "
        else:
            conditions += " AND la.custom_excess_leave_status = %(action_status)s "
        values["action_status"] = filters.get("action_status")

    data = frappe.db.sql(
        f"""
        SELECT
            la.employee,
            la.employee_name,
            emp.department,
            la.leave_type,
            la.name AS allocation,
            la.total_leaves_allocated AS current_balance,
            lt.maximum_carry_forwarded_leaves AS carry_over_limit,
            la.custom_excess_leave_days AS excess_days,
            COALESCE(la.custom_excess_leave_status, 'Pending') AS action_status,
            la.custom_carry_forward_days AS carry_forward_days,
            la.custom_lapsed_leave_days AS lapsed_days,
            la.custom_decision_date AS decision_date,
            la.custom_decided_by AS decided_by
        FROM `tabLeave Allocation` la
        LEFT JOIN `tabEmployee` emp ON emp.name = la.employee
        LEFT JOIN `tabLeave Type` lt ON lt.name = la.leave_type
        {conditions}
        ORDER BY la.employee ASC, la.from_date DESC
        """,
        values,
        as_dict=1,
    )

    for row in data:
        if row.excess_days is None and row.current_balance and row.carry_over_limit:
            row.excess_days = flt(row.current_balance) - flt(row.carry_over_limit)
            if row.excess_days < 0:
                row.excess_days = 0
        if row.excess_days is None:
            row.excess_days = 0

    data = [row for row in data if flt(row.excess_days) > 0]

    return data
