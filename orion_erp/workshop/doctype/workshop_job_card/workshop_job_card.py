import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


ACTIVE_STATUSES = {
    "Inspection",
    "Estimate",
    "Approved",
    "Planned",
    "Awaiting Parts",
    "In Progress",
    "External Repair",
    "Work Completed",
    "Quality Control",
    "Ready for Release",
}

ALLOWED_TRANSITIONS = {
    None: {"Inspection"},
    "Inspection": {"Estimate", "Cancelled"},
    "Estimate": {"Approved", "Cancelled"},
    "Approved": {"Planned", "Awaiting Parts", "In Progress", "Cancelled"},
    "Planned": {"Awaiting Parts", "In Progress", "Cancelled"},
    "Awaiting Parts": {"Planned", "In Progress", "Cancelled"},
    "In Progress": {"Awaiting Parts", "External Repair", "Work Completed", "Cancelled"},
    "External Repair": {"In Progress", "Work Completed", "Cancelled"},
    "Work Completed": {"In Progress", "Quality Control"},
    "Quality Control": {"In Progress", "Ready for Release"},
    "Ready for Release": {"Quality Control", "Released"},
    "Released": {"Financially Closed"},
    "Financially Closed": set(),
    "Cancelled": set(),
}


class WorkshopJobCard(Document):
    def before_validate(self):
        self.check_in = self.check_in or now_datetime()
        self._set_vehicle_details()
        self._calculate_costs()
        self._remember_previous_vehicle_state()

    def validate(self):
        self._validate_asset_link()
        self._validate_odometer()
        self._validate_status_transition()
        self._validate_status_authority()
        self._validate_no_overlapping_job()
        self._validate_inspection_completion()

    def on_update(self):
        previous = self.get_doc_before_save()
        previous_status = previous.status if previous else None
        if self.status in ACTIVE_STATUSES and previous_status not in ACTIVE_STATUSES:
            frappe.db.set_value("Vehicle", self.vehicle, "custom_state", "Workshop")
        elif self.status in {"Released", "Cancelled"} and previous_status in ACTIVE_STATUSES:
            self._restore_vehicle_state()
            if self.status == "Released" and not self.check_out:
                self.db_set("check_out", now_datetime(), update_modified=False)

    def on_trash(self):
        if self.status in ACTIVE_STATUSES:
            self._restore_vehicle_state()

    def _set_vehicle_details(self):
        if not self.vehicle:
            return
        vehicle = frappe.db.get_value(
            "Vehicle",
            self.vehicle,
            ["custom_company", "custom_ownership_status", "custom_asset_mapping"],
            as_dict=True,
        )
        if not vehicle:
            return
        self.company = self.company or vehicle.custom_company
        self.vehicle_ownership_status = vehicle.custom_ownership_status
        self.asset = self.asset or vehicle.custom_asset_mapping

    def _remember_previous_vehicle_state(self):
        if self.vehicle and not self.previous_vehicle_state and self.status in ACTIVE_STATUSES:
            self.previous_vehicle_state = frappe.db.get_value("Vehicle", self.vehicle, "custom_state") or "Idle"

    def _restore_vehicle_state(self):
        if not self.vehicle:
            return
        state = self.previous_vehicle_state or "Idle"
        frappe.db.set_value("Vehicle", self.vehicle, "custom_state", state)

    def _validate_asset_link(self):
        if not self.vehicle or not self.asset:
            return
        mapped_asset = frappe.db.get_value("Vehicle", self.vehicle, "custom_asset_mapping")
        if mapped_asset and mapped_asset != self.asset:
            frappe.throw(_("Asset {0} is not mapped to Vehicle {1}.").format(self.asset, self.vehicle))

    def _validate_odometer(self):
        if self.odometer_out and self.odometer_in and self.odometer_out < self.odometer_in:
            frappe.throw(_("Odometer Out cannot be less than Odometer In."))

    def _validate_status_transition(self):
        previous = self.get_doc_before_save()
        previous_status = previous.status if previous else None
        if self.status == previous_status:
            return
        allowed = ALLOWED_TRANSITIONS.get(previous_status, set())
        if self.status not in allowed:
            frappe.throw(
                _("Workshop Job Card cannot move from {0} to {1}.").format(
                    previous_status or _("New"), self.status
                )
            )

    def _validate_status_authority(self):
        previous = self.get_doc_before_save()
        previous_status = previous.status if previous else None
        if self.status == previous_status:
            return
        roles = set(frappe.get_roles())
        managers = {"Workshop Manager", "System Manager"}
        supervisors = managers | {"Workshop Supervisor"}
        if self.status in {"Approved", "Released"} and not roles.intersection(supervisors):
            frappe.throw(_("Workshop Supervisor or Workshop Manager approval is required."), frappe.PermissionError)
        if self.status in {"Cancelled", "Financially Closed"} and not roles.intersection(managers):
            frappe.throw(_("Workshop Manager approval is required."), frappe.PermissionError)

    def _validate_no_overlapping_job(self):
        if not self.vehicle or self.status not in ACTIVE_STATUSES:
            return
        filters = {
            "vehicle": self.vehicle,
            "status": ["in", list(ACTIVE_STATUSES)],
            "docstatus": ["<", 2],
        }
        if self.name:
            filters["name"] = ["!=", self.name]
        existing = frappe.db.get_value("Workshop Job Card", filters, "name")
        if existing:
            frappe.throw(
                _("Vehicle {0} already has active Workshop Job Card {1}.").format(self.vehicle, existing)
            )

    def _validate_inspection_completion(self):
        if self.status not in {"Ready for Release", "Released"}:
            return
        incomplete = [row.idx for row in self.inspections if row.result == "Not Inspected"]
        if incomplete:
            frappe.throw(_("Complete all inspection rows before releasing the vehicle."))

    def _calculate_costs(self):
        self.parts_cost = sum(flt(row.qty) * flt(row.rate) for row in self.parts)
        for row in self.parts:
            row.amount = flt(row.qty) * flt(row.rate)
        self.labour_cost = sum(flt(row.labour_cost) for row in self.tasks)
        self.external_cost = sum(flt(row.amount) for row in self.external_services)
        self.actual_cost = flt(self.parts_cost) + flt(self.labour_cost) + flt(self.external_cost) + flt(self.overhead_cost)
        self.charge_variance = flt(self.internal_charge) - flt(self.actual_cost)
