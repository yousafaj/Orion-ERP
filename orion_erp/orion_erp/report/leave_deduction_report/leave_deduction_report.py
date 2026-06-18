import frappe
from frappe.utils import getdate, flt, add_days


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
            ss.payment_days
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

    slip_map = {}
    for s in slips:
        twd = flt(s.total_working_days)
        total_default = earning_map.get(s.salary_slip, 0)
        per_day_rate = total_default / twd if twd > 0 else 0

        month_key = (s.employee, getdate(s.start_date).month, getdate(s.start_date).year)
        slip_map[month_key] = {
            "salary_slip": s.salary_slip,
            "per_day_rate": per_day_rate,
            "start_date": s.start_date,
            "end_date": s.end_date,
        }

    return slip_map, slips


def get_grouped_absent_periods(employee, start_date, end_date):
    """Fetch absent attendance and group consecutive dates into periods."""
    records = frappe.db.sql(
        """
        SELECT att.attendance_date
        FROM `tabAttendance` att
        WHERE att.employee = %(employee)s
          AND att.attendance_date BETWEEN %(start)s AND %(end)s
          AND att.docstatus = 1
          AND att.status = 'Absent'
        ORDER BY att.attendance_date
        """,
        {"employee": employee, "start": start_date, "end": end_date},
        as_dict=1,
    )

    if not records:
        return []

    periods = []
    current_start = records[0].attendance_date
    current_end = records[0].attendance_date

    for i in range(1, len(records)):
        d = records[i].attendance_date
        if d == add_days(current_end, 1):
            current_end = d
        else:
            periods.append((current_start, current_end))
            current_start = d
            current_end = d

    periods.append((current_start, current_end))
    return periods


def get_data(filters):
    filters = filters or {}
    data = []

    slip_map, slips = get_salary_slip_map(filters)
    if not slips:
        return data

    # Build employee_name lookup
    emp_name_map = {s.employee: s.employee_name for s in slips}

    for month_key, slip_info in slip_map.items():
        emp = month_key[0]
        month_label = getdate(slip_info["start_date"]).strftime("%B %Y")
        per_day_rate = slip_info["per_day_rate"]
        salary_slip_name = slip_info["salary_slip"]
        slip_start = slip_info["start_date"]
        slip_end = slip_info["end_date"]

        # LWP leave applications for this employee in the salary slip period
        lwp_leaves = frappe.db.sql(
            """
            SELECT
                la.from_date,
                la.to_date,
                la.total_leave_days,
                la.leave_type
            FROM `tabLeave Application` la
            INNER JOIN `tabLeave Type` lt ON lt.name = la.leave_type
            WHERE la.employee = %(employee)s
              AND la.docstatus = 1
              AND la.status = 'Approved'
              AND lt.is_lwp = 1
              AND la.from_date <= %(slip_end)s
              AND la.to_date >= %(slip_start)s
            ORDER BY la.from_date
            """,
            {"employee": emp, "slip_start": slip_start, "slip_end": slip_end},
            as_dict=1,
        )

        emp_name = emp_name_map.get(emp, "")

        for leave in lwp_leaves:
            from_date = max(getdate(leave.from_date), getdate(slip_start))
            to_date = min(getdate(leave.to_date), getdate(slip_end))
            days = flt(leave.total_leave_days)

            data.append({
                "employee": emp,
                "employee_name": emp_name,
                "leave_type": "Leave without pay",
                "from_date": from_date,
                "to_date": to_date,
                "total_leaves_deduction": days,
                "amount": per_day_rate * days,
                "month_of_deduction": month_label,
                "deduction_ref": salary_slip_name,
            })

        absent_periods = get_grouped_absent_periods(emp, slip_start, slip_end)
        for from_date, to_date in absent_periods:
            days = flt((getdate(to_date) - getdate(from_date)).days) + 1
            data.append({
                "employee": emp,
                "employee_name": emp_name,
                "leave_type": "Absent",
                "from_date": from_date,
                "to_date": to_date,
                "total_leaves_deduction": days,
                "amount": per_day_rate * days,
                "month_of_deduction": month_label,
                "deduction_ref": salary_slip_name,
            })

    data.sort(key=lambda r: (
        r["employee_name"] or "",
        r["from_date"] or getdate("1900-01-01"),
        r["leave_type"] == "Absent",
    ))

    return data
