import frappe


DOCTYPES_TO_REMOVE = [
    "Traffic Fine or Accident",
    "Accident Logs",
    "Salik or Darbs",
    "Fines cdt",
]


def execute():
    """Remove the Traffic Fine or Accident, Accident Logs, Salik or Darbs, and
    Fines cdt doctypes. Their directories have been removed from the app
    source, but `bench migrate` does not drop DocType records, their
    underlying tables, Workspace Link entries, or DocType Link (Connections-
    tab) entries on its own — this patch does that cleanup.

    Idempotent: each step checks existence first, so re-running on an
    already-cleaned site is a no-op.
    """
    # Remove workspace links first (Frappe doesn't cascade these on DocType delete).
    workspace_links = frappe.get_all(
        "Workspace Link",
        filters={"link_to": ["in", DOCTYPES_TO_REMOVE]},
        pluck="name",
    )
    for name in workspace_links:
        frappe.delete_doc("Workspace Link", name, ignore_missing=True, force=True)

    # Remove DocType Link rows (the "Connections" tab entries shown on parent
    # doctype forms like Vehicle and Driver). Fixture removal doesn't delete
    # these — they have to be explicitly purged.
    doctype_links = frappe.get_all(
        "DocType Link",
        filters={"link_doctype": ["in", DOCTYPES_TO_REMOVE]},
        pluck="name",
    )
    for name in doctype_links:
        frappe.delete_doc("DocType Link", name, ignore_missing=True, force=True)

    # Delete each DocType. Frappe's DocType.on_trash cascades:
    #   - removes DocPerm rows linked via parent
    #   - removes related Custom Field / Property Setter records
    # Note: with force=True, the underlying `tab<DocType>` table is NOT dropped
    # automatically, so we do that explicitly below.
    for doctype in DOCTYPES_TO_REMOVE:
        if frappe.db.exists("DocType", doctype):
            frappe.delete_doc("DocType", doctype, ignore_missing=True, force=True)

    # Drop the underlying tables explicitly. Backtick-quoted to handle spaces.
    for doctype in DOCTYPES_TO_REMOVE:
        table = f"tab{doctype}"
        # Check if table exists before DROP (idempotency on already-cleaned sites).
        if frappe.db.sql("SHOW TABLES LIKE %s", (table,)):
            frappe.db.sql(f"DROP TABLE `{table}`")

    frappe.clear_cache()
