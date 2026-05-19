import frappe


def execute():

    if frappe.db.exists(
        "Report",
        "Employee Deduction Report"
    ):

        frappe.db.set_value(
            "Report",
            "Employee Deduction Report",
            "add_total_row",
            1
        )