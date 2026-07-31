import frappe
from frappe import _
from frappe.utils import getdate, add_months, add_days


def _get_configured_leave_type():
    settings = frappe.get_single("Orion Settings")
    return getattr(settings, "hajj_umrah_leave_type", None)


def allocate_hajj_umrah_yearly_for_all():
    leave_type_name = _get_configured_leave_type()
    if not leave_type_name:
        return

    eligible_religions_str = getattr(
        frappe.get_single("Orion Settings"), "hajj_umrah_eligible_religions", None
    ) or "Muslim"
    eligible_religions = [r.strip() for r in eligible_religions_str.split(",") if r.strip()]

    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "date_of_joining": ["!=", ""],
            "custom_religion": ["in", eligible_religions]
        },
        fields=["name", "date_of_joining"]
    )

    today = getdate()
    allocated = 0

    for emp in employees:
        if auto_allocate_for_year(emp.name, getdate(emp.date_of_joining), today):
            allocated += 1

    if allocated:
        frappe.log_error(
            f"Hajj/Umrah yearly allocation created for {allocated} employee(s)",
            "Hajj/Umrah Allocation"
        )


def auto_allocate_for_year(employee, doj, today):
    leave_type_name = _get_configured_leave_type()
    if not leave_type_name:
        return False

    leave_type = frappe.db.get_value("Leave Type", {"leave_type_name": leave_type_name}, "name")
    if not leave_type:
        return False

    has_approved = frappe.db.exists("Leave Application", {
        "employee": employee,
        "leave_type": leave_type_name,
        "docstatus": 1,
        "status": "Approved"
    })
    if has_approved:
        return False

    max_days = frappe.get_value("Leave Type", leave_type, "max_leaves_allowed") or 30

    completed = (today.year - doj.year) * 12 + (today.month - doj.month)
    if today.day < doj.day:
        completed -= 1
    completed = max(0, completed)

    year_start_offset = (completed // 12) * 12
    effective_from = add_months(doj, year_start_offset)
    effective_to = add_days(add_months(doj, year_start_offset + 12), -1)

    exists = frappe.db.exists("Leave Allocation", {
        "employee": employee,
        "leave_type": leave_type_name,
        "from_date": effective_from,
        "to_date": effective_to,
        "docstatus": 1
    })
    if exists:
        return False

    prev_year_end = add_days(add_months(doj, year_start_offset), -1)
    prev_allocations = frappe.get_all("Leave Allocation", {
        "employee": employee,
        "leave_type": leave_type_name,
        "to_date": ["<=", prev_year_end],
        "docstatus": 1,
        "expired": 0
    }, pluck="name")

    for alloc_name in prev_allocations:
        alloc = frappe.get_doc("Leave Allocation", alloc_name)
        alloc.expired = 1
        alloc.flags.ignore_permissions = True
        alloc.save()

    allocation = frappe.get_doc({
        "doctype": "Leave Allocation",
        "employee": employee,
        "leave_type": leave_type_name,
        "from_date": effective_from,
        "to_date": effective_to,
        "new_leaves_allocated": max_days,
        "carry_forward": 0,
    })
    allocation.insert(ignore_permissions=True)
    allocation.submit()

    return True
