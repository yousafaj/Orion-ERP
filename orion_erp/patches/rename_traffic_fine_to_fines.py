import frappe


def execute():
    """Rename the 'Traffic Fine or Accident' doctype to 'Fines' (data-preserving).

    Registered under [pre_model_sync] so the table is renamed to `tabFines` BEFORE the
    new fines.json syncs onto it — otherwise model sync would create an empty duplicate.
    `frappe.rename_doc` carries existing records, child-table `parenttype`, and Link-field
    references across. Guarded + idempotent: safe on fresh sites and on re-run.
    """
    if frappe.db.exists("DocType", "Traffic Fine or Accident") and not frappe.db.exists("DocType", "Fines"):
        frappe.rename_doc("DocType", "Traffic Fine or Accident", "Fines", force=True)
        frappe.clear_cache(doctype="Fines")
