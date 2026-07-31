import frappe
from frappe import _
from frappe.utils import getdate, add_days, add_months


def create_leave_policy_assignment(doc, method):
    if not doc.date_of_joining:
        return

    effective_from, effective_to = _get_effective_period(doc.date_of_joining)

    existing_current = frappe.db.get_value("Leave Policy Assignment", {
        "employee": doc.name,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "docstatus": 1
    }, "name")

    if existing_current:
        old_policy = frappe.db.get_value("Employee", doc.name, "custom_leave_policy")
        if not old_policy:
            lpa_policy = frappe.db.get_value("Leave Policy Assignment", existing_current, "leave_policy")
            if lpa_policy:
                frappe.db.set_value("Employee", doc.name, "custom_leave_policy", lpa_policy)
        return

    leave_policy = _get_leave_policy_for_employee(doc)
    if not leave_policy:
        return

    _validate_no_conflicting_allocations(doc, leave_policy, effective_from, effective_to)
    _create_and_submit_lpa(doc, leave_policy, effective_from, effective_to)


def _get_leave_policy_for_employee(doc):
    custom = doc.get("custom_leave_policy") if isinstance(doc, dict) else getattr(doc, "custom_leave_policy", None)
    if custom:
        return custom

    gender = doc.get("gender") if isinstance(doc, dict) else getattr(doc, "gender", None)
    if gender:
        settings = frappe.get_single("Orion Settings")
        for row in settings.leave_policy_by_gender or []:
            if row.gender == gender:
                return row.leave_policy

    return custom


def _get_effective_period(date_of_joining):
    doj = getdate(date_of_joining)
    today_date = getdate()

    completed_months = (today_date.year - doj.year) * 12 + (today_date.month - doj.month)
    if today_date.day < doj.day:
        completed_months -= 1
    completed_months = max(0, completed_months)

    year_start_offset = (completed_months // 12) * 12
    effective_from = add_months(doj, year_start_offset)
    effective_to = add_days(add_months(doj, year_start_offset + 12), -1)
    return effective_from, effective_to


def _validate_no_conflicting_allocations(doc, leave_policy, effective_from, effective_to):
    leave_policy_doc = frappe.get_doc("Leave Policy", leave_policy)
    conflicting = []

    for detail in leave_policy_doc.leave_policy_details:
        if frappe.db.exists("Leave Allocation", {
            "employee": doc.name,
            "leave_type": detail.leave_type,
            "from_date": effective_from,
            "to_date": effective_to,
            "docstatus": 1,
            "expired": 0
        }):
            conflicting.append(detail.leave_type)

    if conflicting:
        frappe.throw(
            _("Leave Allocation(s) already exist for {0} for leave type(s): {1} for period {2} to {3}. Cancel existing allocations before assigning a new leave policy.").format(
                frappe.bold(doc.name),
                frappe.bold(", ".join(conflicting)),
                frappe.bold(str(effective_from)),
                frappe.bold(str(effective_to))
            ),
            title=_("Existing Leave Allocations Found")
        )


def _create_and_submit_lpa(doc, leave_policy, effective_from, effective_to):
    lpa = frappe.new_doc("Leave Policy Assignment")
    lpa.employee = doc.name
    lpa.leave_policy = leave_policy
    lpa.effective_from = effective_from
    lpa.effective_to = effective_to
    lpa.carry_forward = 0
    lpa.insert(ignore_permissions=True)
    lpa.submit()

    employee_name = doc.name if not isinstance(doc, dict) else doc.get("name")
    frappe.db.set_value("Employee", employee_name, "custom_leave_policy", leave_policy)


def auto_renew_leave_policy_assignments():
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "company", "date_of_joining", "gender", "custom_leave_policy"]
    )
    today_date = getdate()

    for emp in employees:
        leave_policy = _get_leave_policy_for_employee(emp)
        if not leave_policy:
            continue

        effective_from, effective_to = _get_effective_period(emp.date_of_joining)
        try:
            _renew_single_employee_lpa(emp, leave_policy, effective_from, effective_to)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Leave Policy Renewal Failed - {emp.name}"
            )


def _renew_single_employee_lpa(emp, leave_policy, effective_from, effective_to):
    existing_lpa = frappe.db.get_value("Leave Policy Assignment", {
        "employee": emp.name,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "docstatus": 1
    }, "name")
    if existing_lpa:
        return

    leave_policy_doc = frappe.get_doc("Leave Policy", leave_policy)
    for detail in leave_policy_doc.leave_policy_details:
        if frappe.db.exists("Leave Allocation", {
            "employee": emp.name,
            "leave_type": detail.leave_type,
            "from_date": ["<=", effective_to],
            "to_date": [">=", effective_from],
            "docstatus": ["in", [0, 1]],
            "expired": 0
        }):
            return

    lpa = frappe.new_doc("Leave Policy Assignment")
    lpa.employee = emp.name
    lpa.leave_policy = leave_policy
    lpa.effective_from = effective_from
    lpa.effective_to = effective_to
    lpa.carry_forward = 0
    lpa.insert(ignore_permissions=True)
    lpa.submit()

    frappe.db.set_value("Employee", emp.name, "custom_leave_policy", leave_policy)
