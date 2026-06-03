# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from orion_erp.orion_erp.doctype.monthly_billing.monthly_billing import rental_on_date


class MaintenanceActivity(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from orion_erp.orion_erp.doctype.maintenance__scheduling.maintenance__scheduling import (
            MaintenanceScheduling,
        )

        amended_from: DF.Link | None
        customer: DF.Link | None
        date: DF.Date | None
        detail: DF.Table[MaintenanceScheduling]
        driver: DF.Link | None
        employment_type: DF.Link | None
        project: DF.Link | None
        shift: DF.Link | None
        vehicle: DF.Link | None
        vehicle_type: DF.Data | None
    # end: auto-generated types

    def validate(self):
        # Auto-fill Customer from the vehicle's rental on this date (shown directly,
        # no need to open the Project). Leaves a manually-set customer alone.
        if not self.customer and self.vehicle and self.date:
            rental = rental_on_date(self.vehicle, self.date)
            if rental:
                self.customer = rental.customer
                self.project = rental.project_to

    def on_submit(self):
        # The vehicle is physically in the workshop while this activity is open.
        if self.vehicle:
            veh = frappe.get_doc("Vehicle", self.vehicle)
            veh.custom_state = "Workshop"
            veh.save(ignore_permissions=True)

    def on_cancel(self):
        if self.vehicle:
            self._restore_vehicle_state()

    def _restore_vehicle_state(self):
        """Back to With Client if a rental is still active, else Idle. (Billing
        days are independent of workshop time — state reflects availability only.)"""
        veh = frappe.get_doc("Vehicle", self.vehicle)
        active_rental = frappe.db.exists(
            "Vehicle Movement",
            {"vehicle": self.vehicle, "docstatus": 1, "rental_status": "Active"},
        )
        veh.custom_state = "With Client" if active_rental else "Idle"
        veh.save(ignore_permissions=True)


@frappe.whitelist()
def return_to_service(name):
    """Mark the vehicle back in service (Idle / With Client) once maintenance is done,
    without cancelling the activity record."""
    doc = frappe.get_doc("Maintenance Activity", name)
    if doc.docstatus != 1:
        frappe.throw(_("Maintenance Activity must be submitted."))
    if not doc.vehicle:
        frappe.throw(_("No vehicle on this activity."))
    doc._restore_vehicle_state()
    return doc.vehicle
