import frappe
from frappe import _
from frappe.model.document import Document
from orion_erp.orion_erp.services.driver_assignment import apply_change, validate_change


class DriverMovement(Document):
    def validate(self):
        if not self.vehicle_movement:
            frappe.throw(_("Select a vehicle movement."))
        movement = frappe.get_doc("Vehicle Movement", self.vehicle_movement)
        if self.docstatus == 0:
            movement.check_permission("write")
            if movement.docstatus != 1 or movement.rental_status != "Active":
                frappe.throw(_("Select a submitted active vehicle movement."))
            self.vehicle = movement.vehicle
            self.project = movement.project_to
            if self.is_new():
                self.previous_driver = movement.driver
        else:
            validate_change(self, movement)

    def on_submit(self):
        apply_change(self)

    def before_cancel(self):
        frappe.throw(_("Driver history cannot be cancelled. Record a new change to reverse it."))

    def on_trash(self):
        if self.docstatus == 1:
            frappe.throw(_("Submitted driver history cannot be deleted."))
