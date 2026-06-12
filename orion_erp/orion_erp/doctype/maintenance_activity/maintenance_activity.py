# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MaintenanceActivity(Document):
    # Deprecated for now — workshop time is tracked via the Vehicle Movement
    # "To Workshop" / "Back in Service" off-hire buttons. New records are blocked;
    # the doctype is retained (no production data).
    def validate(self):
        if self.is_new():
            frappe.throw(
                _("Vehicle Maintenance is currently disabled. Use 'To Workshop' on the Vehicle Movement.")
            )
