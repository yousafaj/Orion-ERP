import frappe
from orion_erp.orion_erp.doctype.orion_settings.orion_settings import sync_role_permissions
from orion_erp.orion_erp.validations.cicpa_dashboard import setup_cicpa_workspace_widgets


ORION_FLEET_CARDS = [
    "Un-invoiced Months",
    "LOA Quota Remaining",
    "Vehicles Rent Ending (30d)",
    "Expire in 30 Days",
    "Expire in 60 Days",
    "Expired Certificates",
    "CICPAs Expiring (30 Days)",
    "Expired CICPAs",
    "With Client Vehicles",
    "Idle Vehicles Vehicles",
    "Internal Use Vehicles",
    "Workshop Vehicles",
    "With Client Drivers",
    "Idle Drivers",
]


def after_migrate():
    sync_role_permissions()
    setup_cicpa_workspace_widgets()
    fix_orion_fleet_cards()


def fix_orion_fleet_cards():
    """The Orion Fleet workspace is synced *before* its Number Cards during migrate,
    so the reqd `number_card_name` Link gets nulled on import (cards don't exist yet).
    Re-apply the cards here, after everything is synced. Idempotent."""
    if not frappe.db.exists("Workspace", "Orion Fleet"):
        return
    cards = [c for c in ORION_FLEET_CARDS if frappe.db.exists("Number Card", c)]
    ws = frappe.get_doc("Workspace", "Orion Fleet")
    if [r.number_card_name for r in ws.number_cards] == cards:
        return  # already correct — nothing to do
    ws.number_cards = []
    for c in cards:
        ws.append("number_cards", {"number_card_name": c})
    ws.save(ignore_permissions=True)
