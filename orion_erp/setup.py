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
    "leave_approval_queue.js": "Leave application Approval Queue",
    "leave_approval_queue_hr.js": "Leave Application Approval queue for HR Manager",
    "team_leave_list.js": "Team Leave Lsit",
    "alert_overlapping_leaves.js": "Alert Overlapping Leaves",
}

DASHBOARDS_DIR = os.path.join(os.path.dirname(__file__), "orion_erp", "dashboards")


def after_migrate():
    sync_role_permissions()
    setup_cicpa_workspace_widgets()
    fix_orion_fleet_cards()
    setup_custom_html_blocks()
    setup_hr_manager_dashboard_roles()


def setup_hr_manager_dashboard_roles():
    """Assign HR Manager role to the HR Manager Dashboard workspace.
    Frappe auto-syncs workspace fixtures, but we need to ensure roles are set."""
    if not frappe.db.exists("Workspace", "HR Manager Dashboard"):
        return
    ws = frappe.get_doc("Workspace", "HR Manager Dashboard")
    if not any(r.role == "HR Manager" for r in ws.roles):
        ws.append("roles", {"role": "HR Manager"})
        ws.flags.ignore_permissions = True
        ws.save(ignore_permissions=True)


def setup_custom_html_blocks():
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
