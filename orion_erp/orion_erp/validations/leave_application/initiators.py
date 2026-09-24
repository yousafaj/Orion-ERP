"""Limit Operations' on-behalf leave creation to non-office employees."""

import frappe
from frappe import _


def validate_leave_initiator(doc, method=None):
    if not doc.employee:
        return

    previous = doc.get_doc_before_save() if not doc.is_new() else None
    if (
        previous
        and previous.employee == doc.employee
        and not (doc.custom_sent_for_approval and not previous.custom_sent_for_approval)
    ):
        return

    user = frappe.session.user
    if user == "Administrator":
        return

    roles = set(frappe.get_roles(user))
    if not roles.intersection({"Operation Team", "Operation Manager"}):
        return
    if roles.intersection({"HR User", "HR Manager"}):
        return

    employee = frappe.db.get_value(
        "Employee", doc.employee, ["user_id", "custom_employee_category"], as_dict=True
    )
    if employee and employee.user_id != user and employee.custom_employee_category != "Non-Office":
        frappe.throw(
            _("Operations users can initiate leave for other employees only when the employee is Non-Office.")
        )
