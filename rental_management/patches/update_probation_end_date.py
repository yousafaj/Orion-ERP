import frappe
from frappe.utils import add_days, getdate, cint


def execute():
    """Update custom_probation_end_date for employees based on confirmation date and probation period."""

    # Get required employee fields
    employees = frappe.get_all(
        "Employee",
        fields=["name", "final_confirmation_date", "custom_probation_period"]
    )

    for emp in employees:
        # Calculate probation end date if required fields exist
        if emp.final_confirmation_date and emp.custom_probation_period:
            probation_end_date = add_days(
                getdate(emp.final_confirmation_date),
                cint(emp.custom_probation_period)
            )

            # Update employee record
            frappe.db.set_value(
                "Employee",
                emp.name,
                "custom_probation_end_date",
                probation_end_date
            )