"""Idempotent Workshop setup routines run after site migration."""

import frappe


WORKSHOP_ROLES = (
    "Workshop Manager",
    "Workshop Supervisor",
    "Workshop Team",
)

VEHICLE_PERMISSION_FIELDS = (
    "read",
    "write",
    "create",
    "delete",
    "submit",
    "cancel",
    "amend",
    "report",
    "export",
    "import",
    "share",
    "print",
    "email",
    "select",
)

VEHICLE_READ_ONLY_PERMISSION = {
    fieldname: int(fieldname in {"read", "select"})
    for fieldname in VEHICLE_PERMISSION_FIELDS
}


def before_migrate():
    ensure_workshop_roles()


def after_migrate():
    ensure_workshop_roles()
    ensure_vehicle_read_only_permissions()


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


def ensure_vehicle_read_only_permissions():
    """Allow Workshop roles to find Vehicles without editing the master.

    Every matching custom permission row is normalized because Frappe combines
    permissions from multiple rows. This prevents an older duplicate row from
    accidentally granting write, create, delete, import or export access.
    """
    for role_name in WORKSHOP_ROLES:
        permission_names = frappe.get_all(
            "Custom DocPerm",
            filters={
                "parent": "Vehicle",
                "role": role_name,
                "permlevel": 0,
            },
            pluck="name",
        )

        if not permission_names:
            permission = frappe.get_doc(
                {
                    "doctype": "Custom DocPerm",
                    "parent": "Vehicle",
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": role_name,
                    "permlevel": 0,
                    **VEHICLE_READ_ONLY_PERMISSION,
                }
            )
            permission.flags.ignore_permissions = True
            permission.insert()
            continue

        for permission_name in permission_names:
            frappe.db.set_value(
                "Custom DocPerm",
                permission_name,
                VEHICLE_READ_ONLY_PERMISSION,
                update_modified=False,
            )

    frappe.clear_cache(doctype="Vehicle")
