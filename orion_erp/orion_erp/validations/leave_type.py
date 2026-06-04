import frappe
from frappe import _

def validate_no_casual_leave(doc, method=None):
    if doc.leave_type_name and doc.leave_type_name.strip().lower() == "casual leave":
        frappe.throw(
            _("Casual Leave is not permitted as per UAE labour law. This Leave Type cannot be created.")
        )
