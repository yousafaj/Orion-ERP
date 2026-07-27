import frappe
from frappe import _

def validate_no_casual_leave(doc, method=None):
    if doc.leave_type_name and doc.leave_type_name.strip().lower() == "casual leave":
        frappe.throw(
            _("Casual Leave is not permitted as per UAE labour law. This Leave Type cannot be created.")
        )


def validate_earned_leave_not_with_accrual(doc, method=None):
    if not doc.is_earned_leave:
        return

    settings = frappe.get_single("Orion Settings")
    configured_types = [
        row.leave_type
        for row in (getattr(settings, "leave_types_for_accrual", None) or [])
        if row.leave_type
    ]

    if doc.name in configured_types:
        frappe.throw(
            _("Cannot enable Is Earned Leave for <b>{0}</b>. This leave type is configured in Orion Settings > Leave Configuration > Leave Types for Accrual & Carry Forward. Earned Leave and Accrual cannot be used together.").format(
                doc.leave_type_name or doc.name
            )
        )
