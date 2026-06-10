# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class VehicleMovement(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from orion_erp.orion_erp.doctype.vehicle_off_hire.vehicle_off_hire import VehicleOffHire

        amended_from: DF.Link | None
        contract: DF.Attach | None
        customer: DF.Link | None
        demobilize_date: DF.Date | None
        driver: DF.Link | None
        invoiceable: DF.Check
        loa: DF.Attach | None
        movement_date: DF.Date
        off_hire: DF.Table[VehicleOffHire]
        project_to: DF.Link | None
        rental_status: DF.Literal["Active", "Closed"]
        vehicle: DF.Link
        vehicle_checklist: DF.Attach | None
    # end: auto-generated types

    # -- Validation --------------------------------------------------------
    def validate(self):
        # Customer auto-fills from the project but stays editable.
        if not self.customer and self.project_to:
            self.customer = frappe.db.get_value("Project", self.project_to, "customer")
        self._check_double_booking()
        self._warn_missing_cicpa()

    def _check_double_booking(self):
        """A vehicle/driver can only be on one active rental at a time."""
        for field, label in (("vehicle", _("Vehicle")), ("driver", _("Driver"))):
            value = self.get(field)
            if not value:
                continue
            other = frappe.db.get_value(
                "Vehicle Movement",
                {field: value, "rental_status": "Active", "docstatus": 1, "name": ["!=", self.name or ""]},
                ["name", "project_to"],
                as_dict=True,
            )
            if other:
                frappe.throw(
                    _("{0} {1} is already on an active movement {2} (project {3}). Demobilize it from there first.").format(
                        label, value, other.name, other.project_to or "-"
                    )
                )

    def _warn_missing_cicpa(self):
        """Non-blocking warning when a billable assignment lacks an active pass."""
        if not self.invoiceable:
            return
        if self.vehicle and not _has_active_cicpa("Vehicle", self.vehicle):
            frappe.msgprint(
                _("Vehicle {0} has no active CICPA pass.").format(self.vehicle), indicator="orange", alert=True
            )
        if self.driver and not _has_active_cicpa("Driver", self.driver):
            frappe.msgprint(
                _("Driver {0} has no active CICPA pass.").format(self.driver), indicator="orange", alert=True
            )

    # -- Lifecycle ---------------------------------------------------------
    def on_submit(self):
        self._mobilize()

    def _mobilize(self):
        # db.set_value — never full-save the Vehicle (it would re-validate mandatory
        # custom fields some live vehicles are missing).
        frappe.db.set_value(
            "Vehicle",
            self.vehicle,
            {
                "custom_state": "With Client" if self.invoiceable else "Internal Use",
                "custom_current_customer": self.customer,
                "custom_project": self.project_to,
            },
        )
        if self.driver:
            frappe.db.set_value("Driver", self.driver, "custom_state", "With Client")

    def on_cancel(self):
        self._release()

    def _release(self):
        if self.vehicle:
            frappe.db.set_value(
                "Vehicle",
                self.vehicle,
                {"custom_state": "Idle", "custom_current_customer": None, "custom_project": None},
            )
        if self.driver:
            frappe.db.set_value("Driver", self.driver, "custom_state", "Idle")


def _has_active_cicpa(cicpa_type, name):
    field = "vehicle" if cicpa_type == "Vehicle" else "driver"
    return bool(
        frappe.db.exists(
            "CICPA", {"cicpa_type": cicpa_type, field: name, "cicpa_status": "Active", "docstatus": 1}
        )
    )


@frappe.whitelist()
def demobilize(name, demobilize_date):
    """Close an active rental: free the vehicle + driver and stamp the date."""
    doc = frappe.get_doc("Vehicle Movement", name)
    doc.check_permission("write")
    if doc.docstatus != 1:
        frappe.throw(_("Submit the movement before demobilizing."))
    if doc.rental_status != "Active":
        frappe.throw(_("This rental is already closed."))
    if demobilize_date and doc.movement_date and getdate(demobilize_date) < getdate(doc.movement_date):
        frappe.throw(_("Demobilize date cannot be before the start date."))
    doc._release()
    doc.db_set("demobilize_date", demobilize_date, update_modified=True)
    doc.db_set("rental_status", "Closed", update_modified=True)
    return doc.name


@frappe.whitelist()
def to_workshop(name, from_date):
    """Send the vehicle to the workshop — opens an off-hire period (excluded from billing)."""
    doc = frappe.get_doc("Vehicle Movement", name)
    doc.check_permission("write")
    if doc.rental_status != "Active":
        frappe.throw(_("Only an active rental can send a vehicle to the workshop."))
    if any(not r.to_date for r in doc.off_hire):
        frappe.throw(_("The vehicle is already in the workshop — use 'Back in Service' first."))
    doc.append("off_hire", {"from_date": from_date, "reason": "Workshop"})
    doc.save(ignore_permissions=True)
    frappe.db.set_value("Vehicle", doc.vehicle, "custom_state", "Workshop")
    return doc.name


@frappe.whitelist()
def back_in_service(name, to_date):
    """Close the open off-hire period and return the vehicle to service."""
    doc = frappe.get_doc("Vehicle Movement", name)
    doc.check_permission("write")
    open_row = next((r for r in doc.off_hire if not r.to_date), None)
    if not open_row:
        frappe.throw(_("The vehicle is not currently in the workshop."))
    if to_date and getdate(to_date) < getdate(open_row.from_date):
        frappe.throw(_("Return date cannot be before the workshop start date."))
    # db_set on the child row — modifying a submitted doc's row value directly
    # (avoids the allow-on-submit restriction; the row was added on submit).
    open_row.db_set("to_date", to_date)
    frappe.db.set_value(
        "Vehicle", doc.vehicle, "custom_state", "With Client" if doc.invoiceable else "Internal Use"
    )
    return doc.name
