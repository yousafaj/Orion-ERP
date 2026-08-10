import frappe


def execute():
    settings = frappe.get_single("Orion Settings")
    gender_policy_map = {
        row.gender: row.leave_policy
        for row in (settings.leave_policy_by_gender or [])
        if row.gender and row.leave_policy
    }
    if not gender_policy_map:
        return

    employees = frappe.get_all(
        "Employee",
        fields=["name", "gender", "custom_leave_policy"],
        filters={"gender": ["in", list(gender_policy_map.keys())]}
    )

    for emp in employees:
        leave_policy = gender_policy_map.get(emp.gender)
        if leave_policy and emp.custom_leave_policy != leave_policy:
            frappe.db.set_value("Employee", emp.name, "custom_leave_policy", leave_policy)
