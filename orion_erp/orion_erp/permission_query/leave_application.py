import frappe


def leave_application_query(user):

    if not user:
        user = frappe.session.user

    # Administrator can see all
    if user == "Administrator":
        return ""

    from orion_erp.orion_erp.validations.leave_application import is_leave_override_user
    if is_leave_override_user(user):
        return ""

    return f"""

        (
            `tabLeave Application`.custom_employee_user_id = '{user}'

            OR

            `tabLeave Application`.owner = '{user}'

            OR

            `tabLeave Application`.leave_approver = '{user}'

            OR

            `tabLeave Application`.custom_leave_approver_1 = '{user}'

            OR

            `tabLeave Application`.custom_leave_approver_2 = '{user}'

            OR

            `tabLeave Application`.custom_leave_approver_4 = '{user}'

            OR

            `tabLeave Application`.custom_leave_approver_5 = '{user}'
        )
    """