import frappe
from frappe import _
from frappe.utils import today

from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on


@frappe.whitelist()
def get_employee_leave_balance(employee, leave_type, date=None):
    return get_leave_balance_on(
        employee=employee,
        leave_type=leave_type,
        date=date
    )


@frappe.whitelist()
def get_employee_leave_balances():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name"],
        as_dict=True,
    )

    if not employee:
        return []

    allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee.name,
            "docstatus": 1
        },
        fields=["leave_type", "from_date", "to_date"]
    )

    data = []
    seen = set()

    for row in allocations:
        if row.leave_type in seen:
            continue

        seen.add(row.leave_type)

        balance = get_leave_balance_on(
            employee.name,
            row.leave_type,
            today(),
            consider_all_leaves_in_the_allocation_period=True
        )

        data.append({
            "leave_type": row.leave_type,
            "balance": balance,
            "from_date": row.from_date,
            "to_date": row.to_date,
        })

    return data


@frappe.whitelist()
def get_leaves_taken_this_year():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name"],
        as_dict=True,
    )

    if not employee:
        return []

    today_date = frappe.utils.today()

    leave_period = frappe.get_all(
        "Leave Period",
        filters={
            "from_date": ("<=", today_date),
            "to_date": (">=", today_date),
        },
        fields=["from_date", "to_date"],
        limit=1,
    )

    if leave_period:
        from_date = leave_period[0].from_date
        to_date = leave_period[0].to_date
    else:
        from_date = f"{frappe.utils.nowdate()[:4]}-01-01"
        to_date = f"{frappe.utils.nowdate()[:4]}-12-31"

    LeaveApplication = frappe.qb.DocType("Leave Application")

    query = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.leave_type,
            LeaveApplication.total_leave_days,
        )
        .where(LeaveApplication.employee == employee.name)
        .where(LeaveApplication.status == "Approved")
        .where(LeaveApplication.docstatus != 2)
        .where(LeaveApplication.from_date >= from_date)
        .where(LeaveApplication.to_date <= to_date)
    )

    rows = query.run(as_dict=True)

    grouped = {}
    for row in rows:
        lt = row.leave_type
        grouped[lt] = grouped.get(lt, 0) + (float(row.total_leave_days or 0))

    result = [
        {"leave_type": lt, "days_taken": round(days, 1)}
        for lt, days in grouped.items()
    ]

    result.sort(key=lambda x: x["leave_type"])

    return result


@frappe.whitelist()
def get_pending_leave_applications():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name"],
        as_dict=True,
    )

    if not employee:
        return []

    exclude_statuses = ["Approved", "Rejected", "Cancelled"]

    LeaveApplication = frappe.qb.DocType("Leave Application")

    query = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.name,
            LeaveApplication.leave_type,
            LeaveApplication.from_date,
            LeaveApplication.to_date,
            LeaveApplication.total_leave_days,
            LeaveApplication.status,
            LeaveApplication.workflow_state,
            LeaveApplication.custom_approval_status,
        )
        .where(LeaveApplication.employee == employee.name)
        .where(LeaveApplication.docstatus != 2)
        .where(LeaveApplication.status.notin(exclude_statuses))
    )

    rows = query.run(as_dict=True)

    result = []
    for row in rows:
        status = row.custom_approval_status or row.workflow_state or row.status or "Pending"

        result.append({
            "name": row.name,
            "leave_type": row.leave_type,
            "from_date": str(row.from_date or ""),
            "to_date": str(row.to_date or ""),
            "total_days": float(row.total_leave_days or 0),
            "status": status,
        })

    result.sort(key=lambda x: x["from_date"], reverse=True)

    return result


@frappe.whitelist()
def get_approved_upcoming_leaves():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name"],
        as_dict=True,
    )
    if not employee:
        return []

    today_date = frappe.utils.today()

    LeaveApplication = frappe.qb.DocType("Leave Application")

    rows = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.name,
            LeaveApplication.leave_type,
            LeaveApplication.from_date,
            LeaveApplication.to_date,
            LeaveApplication.total_leave_days,
        )
        .where(LeaveApplication.employee == employee.name)
        .where(LeaveApplication.status == "Approved")
        .where(LeaveApplication.docstatus != 2)
        .where(LeaveApplication.from_date >= today_date)
        .orderby(LeaveApplication.from_date)
    ).run(as_dict=True)

    result = []
    for row in rows:
        result.append({
            "name": row.name,
            "leave_type": row.leave_type,
            "from_date": str(row.from_date or ""),
            "to_date": str(row.to_date or ""),
            "total_days": float(row.total_leave_days or 0),
        })

    return result


@frappe.whitelist()
def get_monthly_leave_accrual():
    from orion_erp.orion_erp.scripts.annual_leave_accrual import (
        get_rules_from_leave_type,
        get_rate_for_month,
        get_completed_months,
        get_configured_leave_types,
    )

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name", "date_of_joining"],
        as_dict=True,
    )
    if not employee:
        return []

    doj = employee.date_of_joining
    if not doj:
        return []

    if isinstance(doj, str):
        from frappe.utils import getdate
        doj = getdate(doj)

    today = frappe.utils.getdate()
    completed_months = get_completed_months(doj, today)
    if completed_months < 1:
        return []

    result = []
    for leave_type in get_configured_leave_types():
        rules = get_rules_from_leave_type(leave_type)
        if not rules:
            continue

        monthly_rate = get_rate_for_month(completed_months, rules)
        if monthly_rate <= 0:
            continue

        result.append({
            "leave_type": leave_type,
            "earned_days": monthly_rate,
        })

    return result


@frappe.whitelist()
def get_carry_forward_leaves():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name", "date_of_joining"],
        as_dict=True,
    )
    if not employee:
        return []

    doj = employee.date_of_joining
    if not doj:
        return []

    if isinstance(doj, str):
        from frappe.utils import getdate
        doj = getdate(doj)

    today = frappe.utils.getdate()
    prev_year = doj.year

    from orion_erp.orion_erp.scripts.annual_leave_accrual import get_completed_months

    completed_months = get_completed_months(doj, today)

    if completed_months >= 12:
        current_year_num = completed_months // 12
        prev_year = doj.year + current_year_num - 1

    import re
    from frappe.utils import flt

    cf_pattern = re.compile(
        r'Carry Forward Year\s+\d+\s*\|\s*Carry Forward:\s*([\d.]+)\s*days'
    )

    allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee.name,
            "docstatus": 1,
            "description": ["like", "%Carry Forward%"],
        },
        fields=["leave_type", "description", "total_leaves_allocated",
                "custom_carry_forward_days"],
    )

    result_map = {}
    for alloc in allocations:
        if flt(alloc.total_leaves_allocated) <= 0 and flt(alloc.custom_carry_forward_days) <= 0:
            continue
        if not alloc.description:
            continue
        matches = cf_pattern.findall(alloc.description)
        for match in matches:
            base_cf = float(match)
            approved_excess = float(alloc.custom_carry_forward_days or 0)
            total_cf = base_cf + approved_excess
            lt = alloc.leave_type
            result_map[lt] = result_map.get(lt, 0) + total_cf

    result = [
        {"leave_type": lt, "carry_forward_days": round(days, 1)}
        for lt, days in result_map.items()
    ]
    result.sort(key=lambda x: x["leave_type"])
    return {"prev_year": prev_year, "data": result}
