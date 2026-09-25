"""Idempotent Workshop setup routines run after site migration."""

import frappe


WORKSHOP_ROLES = (
    "Workshop Manager",
    "Workshop Supervisor",
    "Workshop Team",
)


def after_migrate():
    ensure_workshop_roles()


def ensure_workshop_roles():
    """Create only the role masters required by the Workshop module.

    Role permissions remain version-controlled in each Workshop DocType.
    Existing roles are never modified by this routine.
    """
    for role_name in WORKSHOP_ROLES:
        if frappe.db.exists("Role", role_name):
            continue
        role = frappe.new_doc("Role")
        role.role_name = role_name
        role.desk_access = 1
        role.flags.ignore_permissions = True
        role.insert()
