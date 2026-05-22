import frappe


def execute():
    """Remove the Driver `custom_has_cicpa` and `custom_cicpa` custom fields and
    drop their underlying `tabDriver` columns. Also drop the orphaned
    `contract_year` column on `tabLOA` (field was removed from loa.json but
    Frappe does not auto-drop columns on doctype field removal).

    Idempotent: safe to run on environments where some/all of the cleanup has
    already happened (e.g. the local dev box where this was done manually).
    """
    _delete_custom_field("Driver-custom_has_cicpa")
    _delete_custom_field("Driver-custom_cicpa")

    _drop_column_if_exists("tabDriver", "custom_has_cicpa")
    _drop_column_if_exists("tabDriver", "custom_cicpa")
    _drop_column_if_exists("tabLOA", "contract_year")

    frappe.clear_cache()


def _delete_custom_field(name):
    if frappe.db.exists("Custom Field", name):
        frappe.delete_doc("Custom Field", name, ignore_missing=True, force=True)


def _drop_column_if_exists(table, column):
    cols = frappe.db.sql(
        "SHOW COLUMNS FROM `{table}` LIKE %s".format(table=table),
        (column,),
    )
    if cols:
        frappe.db.sql(
            "ALTER TABLE `{table}` DROP COLUMN `{column}`".format(
                table=table, column=column
            )
        )
