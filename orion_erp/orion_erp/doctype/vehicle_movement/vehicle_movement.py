# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from orion_erp.orion_erp.doctype.driver_movement.utils import (
    assign_driver_shift,
    release_driver_shift,
    reverse_driver_shift,
)


class VehicleMovement(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from orion_erp.orion_erp.doctype.vehicle_movement_driver_shift.vehicle_movement_driver_shift import (
            VehicleMovementDriverShift,
        )

        amended_from: DF.Link | None
        contract: DF.Attach | None
        customer: DF.Link
        demobilize_date: DF.Date | None
        driver_shifts: DF.Table[VehicleMovementDriverShift]
        loa: DF.Attach | None
        location: DF.Link | None
        location_from: DF.Link | None
        location_to: DF.Link | None
        movement_date: DF.Date
        project_id: DF.Link | None
        project_to: DF.Link
        rent_type: DF.Literal["", "Without Driver", "With Driver"]
        rental_status: DF.Literal["Active", "Closed"]
        status: DF.Literal["", "Available for Use", "Mobilise", "Demobilise", "Breakdown"]
        vehicle: DF.Link
        vehicle_checklist: DF.Attach | None
        vehicle_ownership_status: DF.Data | None
        vehicle_state: DF.Data | None
        vehicle_type: DF.Data | None
    # end: auto-generated types

    def validate(self):
        # Fall back to the project's customer if none was entered (the field is
        # editable now, so a manually-set customer is always respected).
        if not self.customer and self.project_to:
            self.customer = frappe.db.get_value("Project", self.project_to, "customer")
        self._validate_driver_shifts()

    def _validate_driver_shifts(self):
        if self.rent_type == "With Driver":
            if not self.driver_shifts:
                frappe.throw(_("Add at least one driver for a With Driver rental."))
            if len(self.driver_shifts) > 2:
                frappe.throw(_("A vehicle can have at most 2 drivers (day / night shift)."))
            seen = set()
            for row in self.driver_shifts:
                key = (row.driver, row.shift)
                if key in seen:
                    frappe.throw(
                        _("Duplicate driver+shift: {0} on {1}.").format(row.driver, row.shift)
                    )
                seen.add(key)
        else:
            # Without Driver — drop any stray rows so they aren't processed.
            self.driver_shifts = []

    # -- Mobilize ----------------------------------------------------------
    def on_submit(self):
        self._mobilize()

    def _mobilize(self):
        if not self.vehicle:
            frappe.throw(_("Vehicle is required."))

        veh = frappe.get_doc("Vehicle", self.vehicle)
        veh.custom_state = "With Client"
        veh.custom_current_customer = self.customer
        veh.custom_current_rent_type = self.rent_type
        veh.custom_project = self.project_to
        if self.location_to:
            veh.custom_last_location = self.location_to
        veh.save(ignore_permissions=True)

        if self.rent_type == "With Driver":
            for row in self.driver_shifts:
                sa_name = assign_driver_shift(
                    vehicle=self.vehicle,
                    driver=row.driver,
                    shift=row.shift,
                    project=self.project_to,
                    source_name=self.name,
                    start_date=self.movement_date,
                )
                if sa_name:
                    row.db_set("shift_assignment", sa_name)

    # -- Cancel ------------------------------------------------------------
    def on_cancel(self):
        if self.rent_type == "With Driver":
            for row in self.driver_shifts:
                reverse_driver_shift(
                    vehicle=self.vehicle,
                    driver=row.driver,
                    shift=row.shift,
                    source_name=self.name,
                    shift_assignment=row.shift_assignment,
                )

        if not self.vehicle:
            return
        veh = frappe.get_doc("Vehicle", self.vehicle)
        veh.custom_state = "Idle"
        veh.custom_current_customer = None
        veh.custom_current_rent_type = None
        veh.custom_project = None
        if self.location_from:
            veh.custom_last_location = self.location_from
        veh.save(ignore_permissions=True)


@frappe.whitelist()
def demobilize(name, demobilize_date):
    """Close an active rental: free the vehicle, release the drivers, and stamp
    the demobilize date. Operations action (a submitted rental stays as one
    record; this just closes its period)."""
    doc = frappe.get_doc("Vehicle Movement", name)
    if doc.docstatus != 1:
        frappe.throw(_("Vehicle Movement must be submitted before demobilizing."))
    if doc.rental_status != "Active":
        frappe.throw(_("This rental is already closed."))
    if demobilize_date and doc.movement_date and getdate(demobilize_date) < getdate(doc.movement_date):
        frappe.throw(_("Demobilize date cannot be before the start date."))

    if doc.rent_type == "With Driver":
        for row in doc.driver_shifts:
            release_driver_shift(
                vehicle=doc.vehicle,
                driver=row.driver,
                shift=row.shift,
                project=doc.project_to,
                source_name=doc.name,
                end_date=demobilize_date,
                shift_assignment=row.shift_assignment,
            )

    if doc.vehicle:
        veh = frappe.get_doc("Vehicle", doc.vehicle)
        veh.custom_state = "Idle"
        veh.custom_current_customer = None
        veh.custom_current_rent_type = None
        veh.custom_project = None
        veh.save(ignore_permissions=True)

    doc.db_set("demobilize_date", demobilize_date, update_modified=True)
    doc.db_set("rental_status", "Closed", update_modified=True)
    return doc.name
