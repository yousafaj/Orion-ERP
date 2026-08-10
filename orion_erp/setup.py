import os
import frappe
from orion_erp.orion_erp.doctype.orion_settings.orion_settings import sync_role_permissions
from orion_erp.orion_erp.validations.cicpa_dashboard import setup_cicpa_workspace_widgets

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
    "emergency_leave_approval_queue.js": "Emergency Leave Approval Queue",
    # HR User Dashboard blocks
    "org_leave_summary.js": "Organisation-wide Leave Summary",
    "employees_on_leave_today.js": "Employees on Leave Today",
    "pending_approvals_48h.js": "Pending Leave Approvals Older Than 48 Hours",
    "missing_medical_certificates.js": "Missing Medical Certificates",
    "leave_encashment_requests.js": "Leave Encashment Requests",
    "pending_leave_status.js": "Pending Leave Application Status",
    "monthly_accrual_status.js": "Monthly Leave Accrual Run Status",
    "current_month_leave_apps.js": "Current Month Leave Applications",
    "rejoining_overdue.js": "Rejoining Overdue",
}

DASHBOARDS_DIR = os.path.join(os.path.dirname(__file__), "orion_erp", "dashboards")

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
    setup_custom_html_blocks()
    setup_hr_manager_dashboard_roles()
    setup_hr_user_dashboard_roles()
    embed_current_month_leave_block()
    embed_rejoining_overdue_block()
    remove_standalone_current_month_workspace()
    create_employee_categories()


EMPLOYEE_CATEGORIES = ["Office", "Non-Office"]


def create_employee_categories():
    for cat in EMPLOYEE_CATEGORIES:
        if not frappe.db.exists("Employee Category", cat):
            doc = frappe.new_doc("Employee Category")
            doc.category_name = cat
            doc.flags.ignore_permissions = True
            doc.insert()


def setup_hr_user_dashboard_roles():
    """Assign HR User role to the HR User Dashboard workspace."""
    if not frappe.db.exists("Workspace", "HR User Dashboard"):
        return
    ws = frappe.get_doc("Workspace", "HR User Dashboard")
    role_name = "HR User"
    if not any(r.role == role_name for r in ws.roles):
        ws.append("roles", {"role": role_name})
        ws.flags.ignore_permissions = True
        ws.save(ignore_permissions=True)
    # Also add "HR Manager" role so managers can see it too
    if not any(r.role == "HR Manager" for r in ws.roles):
        ws.append("roles", {"role": "HR Manager"})
        ws.flags.ignore_permissions = True
        ws.save(ignore_permissions=True)


def setup_hr_manager_dashboard_roles():
    """Assign HR Manager role to the HR Manager Dashboard workspace and
    ensure the Emergency Leave Approval Queue custom block is present."""
    if not frappe.db.exists("Workspace", "HR Manager Dashboard"):
        return
    ws = frappe.get_doc("Workspace", "HR Manager Dashboard")
    changed = False
    if not any(r.role == "HR Manager" for r in ws.roles):
        ws.append("roles", {"role": "HR Manager"})
        changed = True
    block_name = "Emergency Leave Approval Queue"
    if not any(b.custom_block_name == block_name for b in ws.custom_blocks):
        ws.append("custom_blocks", {"custom_block_name": block_name, "label": block_name})
        changed = True
        # Also add to the content JSON layout
        import json
        content = json.loads(ws.content)
        content.append({
            "type": "custom_block",
            "data": {"custom_block_name": block_name, "col": 12}
        })
        ws.content = json.dumps(content)
    if changed:
        ws.flags.ignore_permissions = True
        ws.save(ignore_permissions=True)


def embed_current_month_leave_block():
    """Add 'Current Month Leave Applications' custom block to both
    HR Manager Dashboard and HR User Dashboard workspaces."""
    import json
    block_name = "Current Month Leave Applications"
    for ws_name in ("HR Manager Dashboard", "HR User Dashboard"):
        if not frappe.db.exists("Workspace", ws_name):
            continue
        ws = frappe.get_doc("Workspace", ws_name)
        changed = False
        if not any(b.custom_block_name == block_name for b in ws.custom_blocks):
            ws.append("custom_blocks", {"custom_block_name": block_name, "label": block_name})
            content = json.loads(ws.content)
            content.append({"type": "custom_block", "data": {"custom_block_name": block_name, "col": 12}})
            ws.content = json.dumps(content)
            changed = True
        if changed:
            ws.flags.ignore_permissions = True
            ws.save(ignore_permissions=True)


def embed_rejoining_overdue_block():
    """Add 'Rejoining Overdue' custom block to HR Manager Dashboard workspace."""
    import json
    block_name = "Rejoining Overdue"
    ws_name = "HR Manager Dashboard"
    if not frappe.db.exists("Workspace", ws_name):
        return
    ws = frappe.get_doc("Workspace", ws_name)
    changed = False
    if not any(b.custom_block_name == block_name for b in ws.custom_blocks):
        ws.append("custom_blocks", {"custom_block_name": block_name, "label": block_name})
        content = json.loads(ws.content)
        content.append({"type": "custom_block", "data": {"custom_block_name": block_name, "col": 12}})
        ws.content = json.dumps(content)
        changed = True
    if changed:
        ws.flags.ignore_permissions = True
        ws.save(ignore_permissions=True)


def remove_standalone_current_month_workspace():
    """Remove the standalone 'Current Month Leave Applications' workspace
    since the block is now embedded in HR Manager and HR User dashboards."""
    ws_name = "Current Month Leave Applications"
    if frappe.db.exists("Workspace", ws_name):
        frappe.delete_doc("Workspace", ws_name, force=True, ignore_permissions=True)


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
