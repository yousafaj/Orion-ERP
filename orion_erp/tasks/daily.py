import frappe
from frappe.utils import nowdate, getdate


def daily():
    deactivate_expired_vehicles()


def deactivate_expired_vehicles():
    """Deactivate vehicles that should no longer be active:
      * Owned vehicles whose mapped Asset has been Sold.
      * Rented vehicles whose rent period has ended.

    Ownership lives in `custom_ownership_status` (Owned/Rented). The earlier
    version checked `custom_vehicle_type` (Light/Heavy) by mistake, so this job
    never deactivated anything.
    """
    vehicles = frappe.get_all(
        "Vehicle",
        filters={"custom_status": "Active"},
        fields=["name", "custom_ownership_status", "custom_asset_mapping", "custom_rent_end_date"],
    )

    for v in vehicles:
        deactivate = False

        if v.custom_ownership_status == "Owned" and v.custom_asset_mapping:
            asset_status = frappe.db.get_value("Asset", v.custom_asset_mapping, "status")
            if asset_status == "Sold":
                deactivate = True

        elif v.custom_ownership_status == "Rented" and v.custom_rent_end_date:
            try:
                if getdate(v.custom_rent_end_date) < getdate(nowdate()):
                    deactivate = True
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"daily: bad rent_end_date for Vehicle {v.name}",
                )
                continue

        if deactivate:
            # db.set_value — never full-save the Vehicle (re-validates mandatory custom
            # fields some live vehicles are missing).
            frappe.db.set_value("Vehicle", v.name, "custom_status", "Inactive")
