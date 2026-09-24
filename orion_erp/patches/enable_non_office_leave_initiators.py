"""Give Operations creation access while keeping their existing approval grants."""

import frappe


def execute():
    parent = "Leave Application"
    manager_permission = frappe.db.get_value(
        "Custom DocPerm",
        {"parent": parent, "role": "Operation Manager", "permlevel": 0},
        "name",
    )
    if manager_permission:
        frappe.db.set_value("Custom DocPerm", manager_permission, "create", 1)

    if not frappe.db.exists(
        "Custom DocPerm", {"parent": parent, "role": "Operation Team", "permlevel": 0}
    ):
        frappe.get_doc(
            {
                "doctype": "Custom DocPerm",
                "parent": parent,
                "role": "Operation Team",
                "permlevel": 0,
                "read": 1,
                "write": 1,
                "create": 1,
                "select": 1,
                "submit": 0,
                "cancel": 0,
            }
        ).insert(ignore_permissions=True)

    # Existing company User Permissions may otherwise hide a group's employees
    # or reject their leave forms. Scope additions to these two DocTypes so
    # unrelated company access keeps its existing bounds.
    companies = frappe.get_all(
        "Company", filters={"abbr": ["in", ["OG", "OEST", "OIFM", "OBR"]]}, pluck="name"
    )
    operations_users = set(
        frappe.get_all(
            "Has Role",
            filters={"parenttype": "User", "role": ["in", ["Operation Team", "Operation Manager"]]},
            pluck="parent",
        )
    )
    for user in operations_users:
        if not frappe.db.exists("User Permission", {"user": user, "allow": "Company"}):
            continue
        for company in companies:
            for doctype in ("Employee", "Leave Application"):
                frappe.add_user_permission(
                    "Company", company, user, ignore_permissions=True, applicable_for=doctype
                )

    frappe.clear_cache(doctype=parent)
