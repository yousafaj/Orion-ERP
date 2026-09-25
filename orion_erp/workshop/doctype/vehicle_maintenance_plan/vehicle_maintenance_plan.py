import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, flt, getdate


class VehicleMaintenancePlan(Document):
    def before_validate(self):
        self._set_vehicle_details()
        self._calculate_next_due()

    def validate(self):
        self._validate_schedule_basis()
        self._validate_asset_link()

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

    def _validate_schedule_basis(self):
        if self.schedule_basis in {"Date", "Date and Odometer"} and cint(self.interval_days) <= 0:
            frappe.throw(_("Interval Days must be greater than zero for a date-based plan."))
        if self.schedule_basis in {"Odometer", "Date and Odometer"} and flt(self.interval_km) <= 0:
            frappe.throw(_("Interval KM must be greater than zero for an odometer-based plan."))

    def _validate_asset_link(self):
        if not self.vehicle or not self.asset:
            return
        mapped_asset = frappe.db.get_value("Vehicle", self.vehicle, "custom_asset_mapping")
        if mapped_asset and mapped_asset != self.asset:
            frappe.throw(_("Asset {0} is not mapped to Vehicle {1}.").format(self.asset, self.vehicle))

    def _calculate_next_due(self):
        if self.last_service_date and self.interval_days:
            self.next_due_date = add_days(getdate(self.last_service_date), cint(self.interval_days))
        if self.last_service_odometer is not None and self.interval_km:
            self.next_due_odometer = flt(self.last_service_odometer) + flt(self.interval_km)
