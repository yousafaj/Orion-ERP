import frappe
from frappe.utils import flt


def validate_leave_encashment(doc, method):
	overrides = frappe.flags.get("_leave_encashment_overrides", {})
	if doc.employee in overrides:
		data = overrides[doc.employee]
		doc.encashment_amount = flt(data.get("amount", 0))
		doc.encashment_days = flt(data.get("days", 0))
