import frappe


def execute():
    if not frappe.db.exists("Leave Type", "Annual Leave"):
        return

    leave_type = frappe.get_doc("Leave Type", "Annual Leave")

    if leave_type.get("custom_annual_leave_accrual_rules"):
        return

    defaults = [
        {"label": "Less than 6 months", "from_months": 0, "to_months": 6, "days_per_month": 2.0},
        {"label": "6 months to less than 1 year", "from_months": 6, "to_months": 12, "days_per_month": 2.5},
        {"label": "1 year or more", "from_months": 12, "to_months": 0, "days_per_month": 2.5},
    ]

    for rule in defaults:
        leave_type.append("custom_annual_leave_accrual_rules", rule)

    leave_type.save(ignore_permissions=True)
