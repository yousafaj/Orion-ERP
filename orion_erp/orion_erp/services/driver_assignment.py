"""Employee driver changes with an immutable transaction history."""
import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def validate_change(change, movement):
    movement.check_permission("write")
    if movement.docstatus != 1 or movement.rental_status != "Active":
        frappe.throw(_("Driver changes require a submitted active vehicle movement."))
    if getdate(change.date) != getdate(nowdate()):
        frappe.throw(_("Submit driver changes on their effective date. Historical and future changes cannot be applied."))
    if getdate(change.date) < getdate(movement.movement_date):
        frappe.throw(_("The effective date cannot precede the vehicle movement."))
    if (change.previous_driver or "") != (movement.driver or ""):
        frappe.throw(_("The assigned driver has changed. Reload the movement and try again."))
    if change.mobilization_status == "Demobilize":
        if change.driver or not movement.driver:
            frappe.throw(_("Removal requires an assigned driver and an empty replacement."))
    elif change.mobilization_status in ("Mobilize", "Change Driver"):
        if not change.driver or change.driver == movement.driver:
            frappe.throw(_("Select a different replacement driver."))
        if not frappe.has_permission("Employee", "read", doc=change.driver):
            frappe.throw(_("You cannot access this employee."), frappe.PermissionError)
        employee = frappe.db.get_value("Employee", change.driver,
            ["status", "custom_employee_category", "designation", "employment_type"], as_dict=True)
        if (not employee or employee.status != "Active"
            or employee.custom_employee_category != "Non-Office"
            or "driver" not in (employee.designation or "").lower()):
            frappe.throw(_("Select an active Non-Office Employee with a driver designation."))
        change.employment_type = employee.employment_type
        conflicts = frappe.db.sql("""SELECT name FROM `tabVehicle Movement`
            WHERE driver=%s AND docstatus=1 AND rental_status='Active'
            AND name!=%s LIMIT 1 FOR UPDATE""", (change.driver, movement.name))
        if conflicts:
            frappe.throw(_("This driver is already assigned to another active vehicle movement."))
    else:
        frappe.throw(_("Select a valid driver action."))
    if not (change.reason or "").strip():
        frappe.throw(_("Enter a reason for the driver change."))
    change.vehicle = movement.vehicle
    change.project = movement.project_to


def apply_change(change):
    if change.driver:
        frappe.db.sql("SELECT name FROM `tabEmployee` WHERE name=%s FOR UPDATE", (change.driver,))
    rows = frappe.db.sql("""SELECT driver, docstatus, rental_status FROM `tabVehicle Movement`
        WHERE name=%s FOR UPDATE""", (change.vehicle_movement,), as_dict=True)
    movement = frappe.get_doc("Vehicle Movement", change.vehicle_movement)
    if not rows:
        frappe.throw(_("Vehicle movement no longer exists."))
    for field in ("driver", "docstatus", "rental_status"):
        setattr(movement, field, rows[0][field])
    validate_change(change, movement)
    movement.db_set("driver", change.driver or None, update_modified=True)
    movement.add_comment("Info", _("Driver change recorded in {0} (effective {1}).").format(change.name, change.date))


@frappe.whitelist()
def change_driver(name, driver=None, effective_date=None, reason=None, previous_driver=None):
    movement = frappe.get_doc("Vehicle Movement", name)
    movement.check_permission("write")
    for action in ("create", "submit"):
        if not frappe.has_permission("Driver Movement", action):
            frappe.throw(_("You cannot create and submit driver changes."), frappe.PermissionError)
    if (previous_driver or "") != (movement.driver or ""):
        frappe.throw(_("The assigned driver has changed. Reload the movement and try again."))
    change = frappe.get_doc({"doctype": "Driver Movement", "vehicle_movement": name,
        "date": effective_date or nowdate(), "mobilization_status": "Change Driver" if driver else "Demobilize",
        "previous_driver": previous_driver or None, "driver": driver or None, "reason": reason})
    change.insert()
    change.submit()
    return change.name
