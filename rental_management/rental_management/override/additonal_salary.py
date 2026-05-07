import frappe

def get_additional_salary_permission_query(user):

    if user == "Administrator":
        return ""

    return """
        (`tabAdditional Salary`.custom_auto_generated IS NULL
        OR `tabAdditional Salary`.custom_auto_generated != 1)
    """