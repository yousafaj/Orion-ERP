import frappe


_TARGETS = [
    ("Vehicle-custom_has_cicpa", "custom_has_cicpa"),
    ("Vehicle-custom_cicpa",     "custom_cicpa"),
    ("Vehicle-custom_vehicle_no", "custom_vehicle_no"),
]


def execute():
    """Drop the Vehicle-side CICPA fields (`custom_has_cicpa`, `custom_cicpa`)
    and the discarded `custom_vehicle_no` field. Fixture entries were removed
    in the same change; this patch deletes the Custom Field records and drops
    the underlying `tabVehicle` columns, which fixture sync does not do.

    Idempotent: existence-checked before each delete/drop. Re-running on an
    already-cleaned site is a no-op.
    """
    for cf_name, _column in _TARGETS:
        if frappe.db.exists("Custom Field", cf_name):
            frappe.delete_doc("Custom Field", cf_name, ignore_missing=True, force=True)

    for _cf, column in _TARGETS:
        cols = frappe.db.sql(
            "SHOW COLUMNS FROM `tabVehicle` LIKE %s", (column,)
        )
        if cols:
            frappe.db.sql_ddl(
                f"ALTER TABLE `tabVehicle` DROP COLUMN `{column}`"
            )

    frappe.clear_cache()
