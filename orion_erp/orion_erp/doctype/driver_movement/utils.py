# In your app's appropriate file (e.g., `driver_utils.py`)
import frappe
from frappe import _


# ---------------------------------------------------------------------------
# Shared driver+shift assignment engine.
#
# Originally these lived inside the Driver Movement controller. Driver handling
# is now folded into Vehicle Movement (a vehicle is rented With/Without Driver),
# so the logic is shared here and called by Vehicle Movement's lifecycle. The
# `source_name` parameter is the originating rental (Vehicle Movement) name and
# is stored on the Vehicle/Driver shift child rows.
# ---------------------------------------------------------------------------

def assign_driver_shift(vehicle, driver, shift, project, source_name, start_date):
    """Assign a driver to a shift on a rented vehicle. Mirrors the old Mobilize
    path: guards against double-booking, links the driver+shift onto both the
    Vehicle and Driver child tables, flips the driver to "With Client", and
    creates a submitted Shift Assignment. Returns the Shift Assignment name."""
    vehicle_doc = frappe.get_doc("Vehicle", vehicle)
    driver_doc = frappe.get_doc("Driver", driver)

    active = frappe.get_all(
        "Shift Assignment",
        filters={
            "employee": driver_doc.employee,
            "shift_type": shift,
            "end_date": ["in", [None, ""]],
            "docstatus": 1,
        },
        pluck="name",
    )
    if active:
        frappe.throw(
            _("Driver {0} already has an active {1} shift ({2}). Demobilize it first.").format(
                driver, shift, active[0]
            )
        )

    if len(driver_doc.custom_shifts) >= 2:
        frappe.throw(_("Driver {0} already has 2 active shifts.").format(driver))

    for row in vehicle_doc.custom_driver_shifts:
        if row.driver == driver and row.shift == shift:
            frappe.throw(_("Driver {0} is already on the {1} shift of this vehicle.").format(driver, shift))

    if len(vehicle_doc.custom_driver_shifts) >= 2:
        frappe.throw(_("Vehicle already has 2 driver shifts assigned."))

    vehicle_doc.append("custom_driver_shifts", {"driver": driver, "mobilization": source_name, "shift": shift})
    vehicle_doc.save(ignore_permissions=True)

    driver_doc.custom_state = "With Client"
    driver_doc.append("custom_shifts", {"movement": source_name, "project": project, "shift": shift})
    driver_doc.save(ignore_permissions=True)

    return _create_shift_assignment(driver_doc, shift, start_date)


def _create_shift_assignment(driver_doc, shift, start_date):
    if not driver_doc.employee:
        frappe.throw(_("No employee linked to driver {0}.").format(driver_doc.name))
    employee_doc = frappe.get_doc("Employee", driver_doc.employee)
    sa = frappe.get_doc({
        "doctype": "Shift Assignment",
        "employee": driver_doc.employee,
        "shift_type": shift,
        "status": "Active",
        "start_date": start_date,
        "company": employee_doc.company,
    })
    sa.insert(ignore_permissions=True)
    sa.submit()
    return sa.name


def release_driver_shift(vehicle, driver, shift, project, source_name, end_date, shift_assignment=None):
    """Demobilize a driver: drop the child rows on Vehicle/Driver, set the driver
    Idle when no shifts remain, and end the Shift Assignment (by explicit name
    when known, else by lookup)."""
    vehicle_doc = frappe.get_doc("Vehicle", vehicle)
    driver_doc = frappe.get_doc("Driver", driver)

    vehicle_doc.custom_driver_shifts = [
        r for r in vehicle_doc.custom_driver_shifts
        if not (r.driver == driver and r.shift == shift)
    ]
    vehicle_doc.save(ignore_permissions=True)

    driver_doc.custom_shifts = [
        r for r in driver_doc.custom_shifts
        if not (r.movement == source_name or (r.shift == shift and r.project == project))
    ]
    if not driver_doc.custom_shifts:
        driver_doc.custom_state = "Idle"
    driver_doc.save(ignore_permissions=True)

    names = [shift_assignment] if shift_assignment else frappe.get_all(
        "Shift Assignment",
        filters={
            "employee": driver_doc.employee,
            "shift_type": shift,
            "end_date": ["in", [None, ""]],
            "docstatus": 1,
        },
        pluck="name",
    )
    for name in names:
        sd = frappe.get_doc("Shift Assignment", name)
        sd.end_date = end_date
        sd.status = "Inactive"
        sd.save(ignore_permissions=True)


def reverse_driver_shift(vehicle, driver, shift, source_name, shift_assignment=None):
    """Cancel path: remove the child rows for this rental and cancel the Shift
    Assignment outright (rather than just ending it)."""
    vehicle_doc = frappe.get_doc("Vehicle", vehicle)
    driver_doc = frappe.get_doc("Driver", driver)

    vehicle_doc.custom_driver_shifts = [
        r for r in vehicle_doc.custom_driver_shifts if r.mobilization != source_name
    ]
    vehicle_doc.save(ignore_permissions=True)

    driver_doc.custom_shifts = [
        r for r in driver_doc.custom_shifts if r.movement != source_name
    ]
    if not driver_doc.custom_shifts:
        driver_doc.custom_state = "Idle"
    driver_doc.save(ignore_permissions=True)

    if shift_assignment and frappe.db.exists("Shift Assignment", shift_assignment):
        sd = frappe.get_doc("Shift Assignment", shift_assignment)
        if sd.docstatus == 1:
            sd.cancel()


@frappe.whitelist()
def get_available_drivers(mobilization_status: str):
    drivers = frappe.get_all("Driver", fields=["name", "custom_state", "employee"])

    result = []
    for driver in drivers:
        # Fetch active shift assignment with no end_date
        shift_assignment = frappe.get_all(
            "Shift Assignment",
            filters={
                "employee": driver.employee,
                "end_date": ["in", [None, ""]]
            },
            fields=["shift_type"]
        )

        # No assignment or assignment found
        assigned_shift = shift_assignment[0].shift_type if shift_assignment else None

        # Logic based on mobilization status
        if mobilization_status == "Mobilize":
            if driver.custom_state == "Idle":
                result.append({
                    "name": driver.name,
                    "label": f"{driver.name} — No shift assigned (Idle)"
                })
            elif driver.custom_state == "With Client" and assigned_shift:
                # Allow shift switch
                result.append({
                    "name": driver.name,
                    "label": f"{driver.name} — Shift {assigned_shift} (With Client)"
                })

        elif mobilization_status == "Demobilize":
            if driver.custom_state == "With Client":
                result.append({
                    "name": driver.name,
                    "label": f"{driver.name} — Ready for Demobilization"
                })

    return result
