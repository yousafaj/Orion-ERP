# Driver Movement is deprecated — driver assignment now lives on Vehicle Movement
# (a single optional Driver field). The old shift-assignment engine (assign/release/
# reverse_driver_shift + Shift Assignment creation) has been removed; only the
# available-drivers helper remains for the legacy form.

import frappe


@frappe.whitelist()
def get_available_drivers(mobilization_status: str):
    drivers = frappe.get_all("Driver", fields=["name", "custom_state"])
    result = []
    for driver in drivers:
        if mobilization_status == "Mobilize" and driver.custom_state == "Idle":
            result.append({"name": driver.name, "label": f"{driver.name} — Idle"})
        elif mobilization_status == "Demobilize" and driver.custom_state == "With Client":
            result.append({"name": driver.name, "label": f"{driver.name} — With Client"})
    return result
