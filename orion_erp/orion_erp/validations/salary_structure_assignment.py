import frappe

def validate_ssa_employee_category(doc, method):

    roles = set(frappe.get_roles())

    # remove system roles
    roles.discard("All")
    roles.discard("Guest")

    # get restricted roles from settings
    settings = frappe.get_cached_doc("Orion Settings")

    restricted_roles = {
        d.role for d in settings.role_for_non_office_employee_ssa_access
    } if settings.role_for_non_office_employee_ssa_access else set()

    # get roles that have SSA read access
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

    # roles (excluding restricted ones) that still give SSA access
    other_roles_with_access = (roles - restricted_roles).intersection(permitted_roles)

    # if user has any other role with SSA access, do not restrict
    if other_roles_with_access:
        return

    # apply restriction only if user has restricted role
    if roles.intersection(restricted_roles):

        if not doc.employee:
            return

        emp_category = frappe.db.get_value(
            "Employee",
            doc.employee,
            "custom_employee_category"
        )

        if emp_category != "Non-Office":
            frappe.throw(
                "You can only create Salary Structure Assignment for Non-Office employees."
            )