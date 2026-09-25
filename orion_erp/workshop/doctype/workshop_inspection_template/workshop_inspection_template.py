import frappe
from frappe import _
from frappe.model.document import Document


class WorkshopInspectionTemplate(Document):
    def validate(self):
        if not self.items:
            frappe.throw(_("Add at least one inspection checkpoint."))
