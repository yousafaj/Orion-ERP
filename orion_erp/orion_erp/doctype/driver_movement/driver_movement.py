# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
from frappe import _


class DriverMovement(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        amended_from: DF.Link | None
        date: DF.Date
        driver: DF.Link
        employment_type: DF.Link | None
        mobilization_status: DF.Literal["", "Mobilize", "Demobilize"]
        ownership_status: DF.Data | None
        project: DF.Link
        shift: DF.Link
        vehicle: DF.Link
        vehicle_type: DF.Data | None
    # end: auto-generated types

    def on_submit(self):
        try:                
            self.update_driver_shift_vehicle()
            if self.mobilization_status == "Mobilize":
                self.create_shift_assignment()
            else: # Demobilize
                self.edit_shift_assignment()
        except Exception as e:
            frappe.db.rollback()
            frappe.throw(_(f"Driver Movement submission failed due to: {str(e)}"))

    def update_driver_shift_vehicle(self):
        vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
        driver_doc = frappe.get_doc("Driver", self.driver)
        if self.mobilization_status == "Mobilize":
            shift_assignment = frappe.get_all(
                "Shift Assignment",
                filters={
                    "employee": driver_doc.employee,
                    "shift_type": self.shift,
                    "end_date": ["in", [None, ""]],
                    "docstatus": 1 
                },
                fields=["name", "custom_mobilization"]
            )
            
            if len(shift_assignment) > 0:
                frappe.throw(_(f"Driver already has Shift assignments of shift: {self.shift} with Movement id : {shift_assignment[0].custom_mobilization}. Make Driver demobalization first."))
                
            if not self.vehicle:
                frappe.throw(_("Vehicle is not specified."))

            if not self.driver or not self.shift:
                frappe.throw(_("Driver and Shift must be specified."))

            if len(driver_doc.custom_shifts) == 2:
                frappe.throw(_("Driver already has 2 Shift assignments of vehicles. Make Driver demobalization first."))
            
            for row in vehicle_doc.custom_driver_shifts:
                if row.driver == self.driver and row.shift == self.shift:
                    frappe.throw(_(f"This driver is already assigned to the shift: {self.shift} on this vehicle."))

            if len(vehicle_doc.custom_driver_shifts) == 2:
                frappe.throw(_("Vehicle already has 2 Shift assignments of drivers. Make Driver demobalization first."))
            
            vehicle_doc.append("custom_driver_shifts", {
                "driver": self.driver,
                "mobilization": self.name,
                "shift": self.shift
            })
            vehicle_doc.save(ignore_permissions=True)
        
            driver_doc.custom_state = "With Client"
            driver_doc.append("custom_shifts", {
                "movement": self.name,
                "project": self.project,
                "shift": self.shift
            })
            driver_doc.save(ignore_permissions=True)
        else:  # Demobilize
            found_vehicle = False
            new_vehicle_shifts = []

            # Remove from vehicle
            for row in vehicle_doc.custom_driver_shifts:
                if row.driver == self.driver and row.shift == self.shift:
                    found_vehicle = True
                    continue 
                new_vehicle_shifts.append(row)

            if not found_vehicle:
                frappe.throw(_("No matching driver and shift found on vehicle to demobilize."))

            vehicle_doc.set("custom_driver_shifts", [])
            for idx, row in enumerate(new_vehicle_shifts, start=1):
                row.idx = idx
                vehicle_doc.append("custom_driver_shifts", row)
            vehicle_doc.save(ignore_permissions=True)

            new_driver_shifts = []
            found_driver = False
            for row in driver_doc.custom_shifts:
                if row.movement == self.name or (row.shift == self.shift and row.project == self.project):
                    found_driver = True
                    continue
                new_driver_shifts.append(row)

            if not found_driver:
                frappe.msgprint(_("No matching shift found on driver to demobilize."))
            
            driver_doc.set("custom_shifts", [])
            for idx, row in enumerate(new_driver_shifts, start=1):
                row.idx = idx
                driver_doc.append("custom_shifts", row)
            if len(driver_doc.custom_shifts) == 0:
                driver_doc.custom_state = "Idle"
            driver_doc.save(ignore_permissions=True)

    def create_shift_assignment(self):
        driver_doc = frappe.get_doc("Driver", self.driver)
        if not driver_doc.employee:
            frappe.throw(_("No employee linked to this driver."))

        employee_doc = frappe.get_doc("Employee", driver_doc.employee)

        shift_assignment = frappe.get_doc({
            "doctype": "Shift Assignment",
            "employee": driver_doc.employee,
            "shift_type": self.shift,
            "status": "Active",
            "start_date": self.date,
            "company": employee_doc.company,
            "custom_mobilization": self.name,
            "docstatus": 0
        })

        shift_assignment.insert(ignore_permissions=True)
        shift_assignment.save()
        shift_assignment.submit()
        
    def edit_shift_assignment(self):
        driver_doc = frappe.get_doc("Driver", self.driver)
        if not driver_doc.employee:
            frappe.throw(_("No employee linked to this driver."))

        # Fetch active shift assignment with no end_date
        shift_assignment = frappe.get_all(
            "Shift Assignment",
            filters={
                "employee": driver_doc.employee,
                "shift_type": self.shift,
                "end_date": ["in", [None, ""]],
                "docstatus": 1 
            },
            fields=["name"]
        )

        if not shift_assignment:
            frappe.throw(_("No active Shift Assignment found to end."))
            return

        # Get and update the document
        shift_doc = frappe.get_doc("Shift Assignment", shift_assignment[0].name)
        shift_doc.end_date = self.date
        shift_doc.status = "Inactive"
        shift_doc.save(ignore_permissions=True)
        frappe.msgprint(_("Shift Assignment {0} ended on {1}").format(shift_doc.name, self.date))

    def on_cancel(self):
        try:
            if self.mobilization_status == "Mobilize":
                self.cancel_mobilization()
            else:  # Demobilize
                self.cancel_demobilization()
        except Exception as e:
            frappe.db.rollback()
            frappe.throw(_(f"Driver Movement cancellation failed due to: {str(e)}"))

    def cancel_mobilization(self):
        """Reverse the mobilization: remove links and cancel shift assignment"""
        vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
        driver_doc = frappe.get_doc("Driver", self.driver)
        
        # Remove from vehicle's custom_driver_shifts
        new_vehicle_shifts = []
        for row in vehicle_doc.custom_driver_shifts:
            if row.mobilization == self.name:
                continue
            new_vehicle_shifts.append(row)
        
        vehicle_doc.set("custom_driver_shifts", [])
        for idx, row in enumerate(new_vehicle_shifts, start=1):
            row.idx = idx
            vehicle_doc.append("custom_driver_shifts", row)
        vehicle_doc.save(ignore_permissions=True)
        
        # Remove from driver's custom_shifts
        new_driver_shifts = []
        for row in driver_doc.custom_shifts:
            if row.movement == self.name:
                continue
            new_driver_shifts.append(row)
        
        driver_doc.set("custom_shifts", [])
        for idx, row in enumerate(new_driver_shifts, start=1):
            row.idx = idx
            driver_doc.append("custom_shifts", row)
        
        # Update driver state if no shifts remain
        if len(driver_doc.custom_shifts) == 0:
            driver_doc.custom_state = "Idle"
        
        driver_doc.save(ignore_permissions=True)
        
        # Cancel the Shift Assignment created by this mobilization
        shift_assignments = frappe.get_all(
            "Shift Assignment",
            filters={
                "custom_mobilization": self.name,
                "docstatus": 1
            },
            fields=["name"]
        )
        
        for sa in shift_assignments:
            shift_doc = frappe.get_doc("Shift Assignment", sa.name)
            shift_doc.cancel()
        
        frappe.msgprint(_("Mobilization cancelled and all related records have been unlinked."))

    def cancel_demobilization(self):
        """Reverse the demobilization: restore links and reactivate shift assignment"""
        vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
        driver_doc = frappe.get_doc("Driver", self.driver)
        
        # Re-add to vehicle's custom_driver_shifts
        vehicle_doc.append("custom_driver_shifts", {
            "driver": self.driver,
            "mobilization": self.name,
            "shift": self.shift
        })
        vehicle_doc.save(ignore_permissions=True)
        
        # Re-add to driver's custom_shifts
        driver_doc.custom_state = "With Client"
        driver_doc.append("custom_shifts", {
            "movement": self.name,
            "project": self.project,
            "shift": self.shift
        })
        driver_doc.save(ignore_permissions=True)
        
        # Reactivate the Shift Assignment (remove end_date, set status back to Active)
        shift_assignments = frappe.get_all(
            "Shift Assignment",
            filters={
                "employee": driver_doc.employee,
                "shift_type": self.shift,
                "end_date": self.date,
                "docstatus": 1
            },
            fields=["name"]
        )
        
        if shift_assignments:
            shift_doc = frappe.get_doc("Shift Assignment", shift_assignments[0].name)
            shift_doc.end_date = None
            shift_doc.status = "Active"
            shift_doc.save(ignore_permissions=True)
            frappe.msgprint(_("Shift Assignment {0} reactivated.").format(shift_doc.name))
        
        frappe.msgprint(_("Demobilization cancelled and driver has been re-linked."))