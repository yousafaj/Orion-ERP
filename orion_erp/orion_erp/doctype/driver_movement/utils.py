# In your app's appropriate file (e.g., `driver_utils.py`)
import frappe
from frappe import _

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
