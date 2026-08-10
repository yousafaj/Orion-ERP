import frappe


def auto_allocate_hajj_umrah(doc, method):
    if not doc.date_of_joining or doc.custom_religion != "Muslim":
        return

    leave_type = _get_hajj_umrah_leave_type()
    if not leave_type:
        return

    if _has_approved_hajj_leave(doc.name, leave_type):
        return
    if _has_existing_allocation(doc.name, leave_type):
        return

    from .leave_policy import _get_effective_period
    effective_from, effective_to = _get_effective_period(doc.date_of_joining)
    max_days = frappe.get_value("Leave Type", leave_type, "max_leaves_allowed") or 21

    allocation = frappe.get_doc({
        "doctype": "Leave Allocation",
        "employee": doc.name,
        "leave_type": leave_type,
        "from_date": effective_from,
        "to_date": effective_to,
        "new_leaves_allocated": max_days,
        "carry_forward": 0,
    })
    allocation.insert(ignore_permissions=True)
    allocation.submit()


def _get_hajj_umrah_leave_type():
    settings = frappe.get_single("Orion Settings")
    leave_type_name = getattr(settings, "hajj_umrah_leave_type", None)
    if not leave_type_name:
        return None
    if not frappe.db.exists("Leave Type", {"leave_type_name": leave_type_name}):
        return None
    return frappe.db.get_value("Leave Type", {"leave_type_name": leave_type_name}, "name")


def _has_approved_hajj_leave(employee, leave_type):
    return frappe.db.exists("Leave Application", {
        "employee": employee,
        "leave_type": leave_type,
        "docstatus": 1,
        "status": "Approved"
    })


def _has_existing_allocation(employee, leave_type):
    return frappe.db.exists("Leave Allocation", {
        "employee": employee,
        "leave_type": leave_type,
        "docstatus": 1
    })
