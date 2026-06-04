import frappe


def execute():
    """Retire the orphaned 'Accident Logs' child doctype (accidents dropped from the Fines flow).

    Only deletes when the table is empty, honouring the project rule against dropping populated
    tables. If rows exist, it's left intact (already unreferenced) and a message is logged.
    """
    if not frappe.db.exists("DocType", "Accident Logs"):
        return
    if frappe.db.count("Accident Logs") == 0:
        frappe.delete_doc("DocType", "Accident Logs", force=True, ignore_permissions=True)
    else:
        frappe.log_error(
            title="remove_accident_logs skipped",
            message="'Accident Logs' still has rows; left intact (unreferenced).",
        )
