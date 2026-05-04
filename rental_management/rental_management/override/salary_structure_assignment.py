import frappe

def get_ssa_permission_query(user):

    roles = set(frappe.get_roles(user))

    # Remove default roles
    roles.discard("All")
    roles.discard("Guest")

    restricted_roles = set()

    settings = frappe.get_single("Orion Settings")

    if settings.role_for_non_office_employee_ssa_access:
        restricted_roles = {
            d.role for d in settings.role_for_non_office_employee_ssa_access
        }

    permitted_roles = set(
        frappe.get_all(
            "DocPerm",
            filters={
                "parent": "Salary Structure Assignment",
                "read": 1
            },
            pluck="role"
        )
    )

    other_roles_with_access = (roles - restricted_roles).intersection(permitted_roles)

    # If ANY other role gives access → FULL access
    if other_roles_with_access:
        return ""

    # If user has restricted role → apply restriction
    if roles.intersection(restricted_roles):
        return """
            `tabSalary Structure Assignment`.employee IN (
                SELECT name FROM `tabEmployee`
                WHERE custom_employee_category = 'Non-Office'
            )
        """

    return ""