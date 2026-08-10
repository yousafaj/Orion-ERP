import frappe


def rejoining_form_query(user):
    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return ""

    return f"""
        (
            `tabRejoining Form`.custom_employee_user_id = '{user}'
            OR
            `tabRejoining Form`.owner = '{user}'
            OR
            `tabRejoining Form`.custom_rejoining_approver_1 = '{user}'
            OR
            `tabRejoining Form`.custom_rejoining_approver_2 = '{user}'
            OR
            `tabRejoining Form`.custom_rejoining_approver_3 = '{user}'
            OR
            `tabRejoining Form`.custom_rejoining_approver_4 = '{user}'
            OR
            `tabRejoining Form`.custom_rejoining_approver_5 = '{user}'
        )
    """
