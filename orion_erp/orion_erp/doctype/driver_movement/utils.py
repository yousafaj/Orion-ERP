import frappe


def get_available_drivers(mobilization_status=None):
    """Compatibility helper using the permission-aware operational Employee master."""
    employees = frappe.get_list("Employee", filters={"status": "Active",
        "custom_employee_category": "Non-Office", "designation": ["like", "%Driver%"]},
        fields=["name", "employee_name"], limit_page_length=1000)
    return [{"name": e.name, "label": e.employee_name} for e in employees]
