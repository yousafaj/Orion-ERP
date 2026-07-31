import frappe
from frappe.utils import getdate, flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Leave Type", "fieldname": "leave_type", "fieldtype": "Data", "width": 180},
        {"label": "From Date", "fieldname": "from_date", "fieldtype": "Date", "width": 110},
        {"label": "To Date", "fieldname": "to_date", "fieldtype": "Date", "width": 110},
        {"label": "Total Leaves Deduction", "fieldname": "total_leaves_deduction", "fieldtype": "Float", "width": 160},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "Month of Deduction", "fieldname": "month_of_deduction", "fieldtype": "Data", "width": 150},
        {"label": "Deduction Ref", "fieldname": "deduction_ref", "fieldtype": "Link", "options": "Salary Slip", "width": 180},
    ]


def get_salary_slip_map(filters):
    """Fetch draft salary slips and return dict keyed by (employee, month, year)."""
    conditions = "ss.docstatus = 0"
    values = {}

    if filters.get("from_date"):
        conditions += " AND ss.start_date >= %(from_date)s"
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions += " AND ss.end_date <= %(to_date)s"
        values["to_date"] = filters["to_date"]
    if filters.get("employee"):
        conditions += " AND ss.employee = %(employee)s"
        values["employee"] = filters["employee"]

    slips = frappe.db.sql(
        f"""
        SELECT
            ss.name AS salary_slip,
            ss.employee,
            ss.employee_name,
            ss.start_date,
            ss.end_date,
            ss.total_working_days,
            ss.payment_days,
            ss.leave_without_pay,
            ss.absent_days
        FROM `tabSalary Slip` ss
        WHERE {conditions}
        ORDER BY ss.employee, ss.start_date
        """,
        values,
        as_dict=1,
    )

    if not slips:
        return {}, []

    slip_names = [s.salary_slip for s in slips]

    # Get sum of default_amount for earnings that depend on payment days
    earning_data = frappe.db.sql(
        """
        SELECT
            sd.parent AS salary_slip,
            SUM(sd.default_amount) AS total_default_amount
        FROM `tabSalary Detail` sd
        WHERE sd.parent IN %(slip_names)s
          AND sd.parentfield = 'earnings'
          AND sd.depends_on_payment_days = 1
        GROUP BY sd.parent
        """,
        {"slip_names": slip_names},
        as_dict=1,
    )

    earning_map = {r.salary_slip: flt(r.total_default_amount) for r in earning_data}

    # Get base from Salary Structure Assignment as fallback for per_day_rate
    emp_list = list(set(s.employee for s in slips))
    ssa_map = {}
    if emp_list:
        all_ssa = frappe.db.sql(
            """
            SELECT employee, base, from_date
            FROM `tabSalary Structure Assignment`
            WHERE docstatus = 1 AND employee IN %(employees)s
            ORDER BY employee, from_date DESC
            """,
            {"employees": emp_list},
            as_dict=1,
        )
        for r in all_ssa:
            if r.employee not in ssa_map:
                ssa_map[r.employee] = flt(r.base)

    slip_map = {}
    for s in slips:
        twd = flt(s.total_working_days)
        total_default = earning_map.get(s.salary_slip, 0)
        per_day_rate = total_default / twd if twd > 0 else 0

        # Fallback: when per_day_rate is 0 (e.g. payment_days = 0 removes earnings rows),
        # use base from Salary Structure Assignment
        if per_day_rate == 0 and twd > 0:
            base = ssa_map.get(s.employee, 0)
            per_day_rate = base / twd if base else 0

        month_key = (s.employee, getdate(s.start_date).month, getdate(s.start_date).year)
        slip_map[month_key] = {
            "salary_slip": s.salary_slip,
            "per_day_rate": per_day_rate,
            "start_date": s.start_date,
            "end_date": s.end_date,
            "leave_without_pay": flt(s.leave_without_pay),
            "absent_days": flt(s.absent_days),
        }

    return slip_map, slips


def get_data(filters):
    filters = filters or {}
    data = []

    slip_map, slips = get_salary_slip_map(filters)
    if not slips:
        return data

    emp_name_map = {s.employee: s.employee_name for s in slips}

    for month_key, slip_info in slip_map.items():
        emp = month_key[0]
        month_label = getdate(slip_info["start_date"]).strftime("%B %Y")
        per_day_rate = slip_info["per_day_rate"]
        salary_slip_name = slip_info["salary_slip"]
        slip_start = slip_info["start_date"]
        slip_end = slip_info["end_date"]
        lwp_days = slip_info["leave_without_pay"]
        absent_days = slip_info["absent_days"]

        emp_name = emp_name_map.get(emp, "")

        if lwp_days:
            data.append({
                "employee": emp,
                "employee_name": emp_name,
                "leave_type": "Leave without pay",
                "from_date": slip_start,
                "to_date": slip_end,
                "total_leaves_deduction": lwp_days,
                "amount": per_day_rate * lwp_days,
                "month_of_deduction": month_label,
                "deduction_ref": salary_slip_name,
            })

        if absent_days:
            data.append({
                "employee": emp,
                "employee_name": emp_name,
                "leave_type": "Absent",
                "from_date": slip_start,
                "to_date": slip_end,
                "total_leaves_deduction": absent_days,
                "amount": per_day_rate * absent_days,
                "month_of_deduction": month_label,
                "deduction_ref": salary_slip_name,
            })

    data.sort(key=lambda r: (
        r["employee_name"] or "",
        r["from_date"] or getdate("1900-01-01"),
        r["leave_type"] == "Absent",
    ))

    return data
