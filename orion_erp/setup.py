import json
import re
import os
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

DASHBOARD_FILES = {
    "leave_balance.js": "My Leave Balance Cards",
    "leaves_taken_this_year.js": "Leaves Taken This Year",
    "pending_leave_apps.js": "Pending Leave Applications",
    "approved_upcoming_leaves.js": "Approved Upcoming Leaves",
    "monthly_leave_accrual.js": "Monthly Leave Accrual Summary",
    "carry_forward_leaves.js": "Carry Forward Leave Summary",
}

DASHBOARDS_DIR = os.path.join(os.path.dirname(__file__), "orion_erp", "dashboards")


def after_migrate():
    sync_role_permissions()
    setup_cicpa_workspace_widgets()
    fix_orion_fleet_cards()
    setup_custom_html_blocks()
    setup_leave_balance_cards()


def setup_custom_html_blocks():
    ws_name = "Employee Leave Dashboard"

    for filename, block_name in DASHBOARD_FILES.items():
        filepath = os.path.join(DASHBOARDS_DIR, filename)
        if not os.path.exists(filepath):
            continue

        with open(filepath) as f:
            script = f.read()

        if frappe.db.exists("Custom HTML Block", block_name):
            doc = frappe.get_doc("Custom HTML Block", block_name)
            doc.script = script
            doc.style = ""
            doc.html = ""
            doc.flags.ignore_permissions = True
            doc.save(ignore_permissions=True)
        else:
            doc = frappe.get_doc({
                "doctype": "Custom HTML Block",
                "custom_block_name": block_name,
                "name": block_name,
                "script": script,
                "style": "",
                "html": "",
            })
            doc.flags.ignore_permissions = True
            doc.flags.ignore_mandatory = True
            doc.db_insert()

    ws_is_new = not frappe.db.exists("Workspace", ws_name)
    if ws_is_new:
        ws = frappe.get_doc({
            "doctype": "Workspace",
            "name": ws_name,
            "label": ws_name,
            "title": ws_name,
            "icon": "fa fa-users",
            "module": "Orion ERP",
            "public": 1,
            "content": "[]",
        })
        ws.flags.ignore_permissions = True
        ws.flags.ignore_mandatory = True
        ws.db_insert()
    ws = frappe.get_doc("Workspace", ws_name)
    ws.flags.ignore_permissions = True

    content = json.loads(ws.content or "[]")
    existing_block_names = {item.get("data", {}).get("custom_block_name") for item in content if item.get("type") == "custom_block"}
    existing_child_names = {b.custom_block_name for b in ws.custom_blocks}

    for _, block_name in DASHBOARD_FILES.items():
        if block_name not in existing_block_names:
            content.append({"type": "custom_block", "data": {"custom_block_name": block_name, "col": 12}})
        if block_name not in existing_child_names:
            ws.append("custom_blocks", {"custom_block_name": block_name, "label": block_name})

    ws.content = json.dumps(content)
    ws.save(ignore_permissions=True)


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


def _normalize_lt(name):
    return re.sub(r'[^a-z0-9_]', '', name.lower().replace(' ', '_').replace('/', '_').replace('-', '_'))


def setup_leave_balance_cards():
    """Create number cards for each leave type for the current employee's dashboard.
    Runs after workspace fixtures are loaded so content can be updated correctly."""
    ws_name = "Employee Leave Dashboard"
    if not frappe.db.exists("Workspace", ws_name):
        return
    leave_types = frappe.get_all("Leave Type", pluck="name")
    if not leave_types:
        return

    ws = frappe.get_doc("Workspace", ws_name)

    # Create number card records for each leave type
    card_name_map = {}
    for lt in leave_types:
        method = f"orion_erp.orion_erp.validations.leave_balance_cards.{_normalize_lt(lt)}_balance"

        # Reuse if already exists by original name or normalized name
        existing = None
        for candidate in (lt, _normalize_lt(lt)):
            if frappe.db.exists("Number Card", candidate):
                existing = candidate
                break
        if existing:
            card_name_map[lt] = existing
            continue

        new_name = _normalize_lt(lt)
        card = frappe.get_doc({
            "doctype": "Number Card",
            "label": lt,
            "name": new_name,
            "module": "Orion ERP",
            "is_standard": 1,
            "is_public": 1,
            "type": "Custom",
            "method": method,
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily",
        })
        card.flags.ignore_permissions = True
        card.flags.ignore_mandatory = True
        card.db_insert()
        card_name_map[lt] = new_name

    # Rebuild workspace content: keep existing blocks, add My Leave Balance section
    content = json.loads(ws.content)
    known_card_names = set(card_name_map.values())
    content = [b for b in content if b.get("id") != "hdr_bal" and not (b.get("type") == "number_card" and b.get("data", {}).get("number_card_name", "") in known_card_names)]

    content.append({"id": "hdr_bal", "type": "header", "data": {"text": "<span class=\"h4\">My Leave Balance</span>", "col": 12}})
    col = max(3, min(6, 12 // max(len(leave_types), 1)))
    for i, lt in enumerate(leave_types):
        content.append({"id": f"nc_lb{i}", "type": "number_card", "data": {"number_card_name": card_name_map[lt], "col": col}})

    ws.content = json.dumps(content)
    ws.number_cards = []
    for lt in leave_types:
        ws.append("number_cards", {"number_card_name": card_name_map[lt]})
    ws.save(ignore_permissions=True)
