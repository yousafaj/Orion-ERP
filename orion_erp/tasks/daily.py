import frappe
from frappe.utils import nowdate, getdate

def daily():
    validate_vehicle()

def validate_vehicle():
    vehicles = frappe.get_all("Vehicle", filters={"custom_status": "Active"}, fields=["name", "custom_vehicle_type", "custom_asset_mapping", "custom_rent_end_date"])

    for v in vehicles:
        if v.custom_vehicle_type == "Owned" and v.custom_asset_mapping:
            asset_status = frappe.db.get_value("Asset", v.custom_asset_mapping, "status")
            if asset_status == "Sold":
                frappe.db.set_value("Vehicle", v.name, "status", "Inactive")
                frappe.db.commit()

        elif v.custom_vehicle_type == "Rented" and v.custom_rent_end_date:
            try:
                rent_end = getdate(v.custom_rent_end_date)
                if rent_end < getdate(nowdate()):
                    frappe.db.set_value("Vehicle", v.name, "status", "Inactive")
                    frappe.db.commit()
            except Exception as e:
                frappe.log_error(f"Error parsing rent_end_date for Vehicle {v.name}: {str(e)}")
