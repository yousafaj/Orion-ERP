import frappe


def execute():
    """Delete the legacy DB-only 'Rental Management' workspace (folded into 'Orion Fleet').

    It was never shipped by the renamed orion_erp app, so migrate neither re-creates nor
    removes it — older benches (RnD/Staging/Prod) still carry the leftover record. This
    idempotent patch removes it everywhere on migrate. The CICPA expiry cards/widget that
    used to live on it are now injected into 'Orion Fleet' instead (setup_cicpa_workspace_widgets).
    """
    if frappe.db.exists("Workspace", "Rental Management"):
        frappe.delete_doc("Workspace", "Rental Management", ignore_permissions=True, force=True)
