import frappe
from frappe.utils import flt


def validate_leave_encashment(doc, method):
	overrides = frappe.flags.get("_leave_encashment_overrides", {})
	if doc.employee in overrides:
		data = overrides[doc.employee]
		doc.encashment_amount = flt(data.get("amount", 0))
		doc.encashment_days = flt(data.get("days", 0))


def on_cancel_leave_encashment(doc, method):
	"""Prevent direct cancellation of Leave Encashment linked to an active Leave Settlement."""
	if doc.custom_leave_settlement_ref:
		docstatus = frappe.db.get_value("Leave Settlement", doc.custom_leave_settlement_ref, "docstatus")
		if docstatus == 1:
			frappe.throw(
				f"Cannot cancel this Leave Encashment directly. "
				f"Please cancel the linked Leave Settlement "
				f"<a href='/app/leave-settlement/{doc.custom_leave_settlement_ref}'>"
				f"{doc.custom_leave_settlement_ref}</a> instead, "
				f"which will automatically cancel this Leave Encashment."
			)
