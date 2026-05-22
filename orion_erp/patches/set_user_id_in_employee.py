import frappe

def execute():
    employees = frappe.get_all(
        "Employee",
        fields=["name", "employee_name", "user_id"],
        filters={"user_id": ["is", "not set"]}
    )

    for emp in employees:
        if not emp.employee_name:
            continue

        user = frappe.db.get_value(
            "User",
            {"full_name": emp.employee_name},
            "name"
        )

        if user:
            frappe.db.set_value("Employee", emp.name, "user_id", user)