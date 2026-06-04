# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DriverMovement(Document):
    # Deprecated — driver assignment now lives on Vehicle Movement (a single
    # optional Driver field). New Driver Movements are blocked; existing records
    # (none in production) remain openable.
    def validate(self):
        if self.is_new():
            frappe.throw(
                _("Driver Movement is deprecated. Assign the driver directly on the Vehicle Movement.")
            )
