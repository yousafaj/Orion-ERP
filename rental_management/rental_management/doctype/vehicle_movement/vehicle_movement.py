# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class VehicleMovement(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        amended_from: DF.Link | None
        contract: DF.Attach | None
        customer: DF.Link | None
        loa: DF.Attach | None
        location: DF.Link | None
        location_from: DF.Link | None
        location_to: DF.Link | None
        movement_date: DF.Date
        project_id: DF.Link | None
        project_to: DF.Link | None
        rent_type: DF.Literal["", "Without Driver", "With Driver"]
        status: DF.Literal["", "Available for Use", "Mobilise", "Demobilise", "Breakdown"]
        vehicle: DF.Link
        vehicle_checklist: DF.Attach | None
        vehicle_ownership_status: DF.Data | None
        vehicle_state: DF.Data | None
        vehicle_type: DF.Data | None
    # end: auto-generated types
    
    def on_submit(self):
        try:
            self.update_vehicle()
        except Exception as e:
            frappe.db.rollback()
            frappe.throw(_(f"Vehicle Movement submission failed due to: {str(e)}"))

    def update_vehicle(self):
        if self.status == "Mobilise":
            if not self.vehicle:
                frappe.throw(_("Vehicle is not specified."))

            frappe.db.set_value("Vehicle", self.vehicle, {
                "custom_last_location": self.location_to,
                "custom_state": "With Client",
                "custom_current_rent_type": self.rent_type,
                "custom_project": self.project_to
            })
            frappe.db.commit()
        elif self.status == "Demobilise" or self.status == "Available for Use":
            if not self.vehicle:
                frappe.throw(_("Vehicle is not specified."))

            frappe.db.set_value("Vehicle", self.vehicle, {
                "custom_last_location": self.location_to,
                "custom_state": "Idle",
                "custom_current_rent_type": None,
                "custom_project": None
            })
            frappe.db.commit()
        elif self.status == "Breakdown":
            if not self.vehicle:
                frappe.throw(_("Vehicle is not specified."))

            frappe.db.set_value("Vehicle", self.vehicle, {
                "custom_last_location": self.location_to,
                "custom_state": "Workshop",
                "custom_current_rent_type": None,
                "custom_project": None
            })
            frappe.db.commit()

    def on_cancel(self):
        try:
            if not self.vehicle:
                return
                
            frappe.db.set_value("Vehicle", self.vehicle, {
                "custom_last_location": self.location_from,
                "custom_state": "Idle",
                "custom_current_rent_type": None,
                "custom_project": None
            })
            frappe.db.commit()
            frappe.msgprint(_("Vehicle {0} has been unlinked and reset.").format(self.vehicle))
        except Exception as e:
            frappe.db.rollback()
            frappe.throw(_(f"Vehicle Movement cancellation failed due to: {str(e)}"))