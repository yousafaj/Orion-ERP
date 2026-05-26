import frappe

def create_air_ticket_entitlement_on_submit(doc, method=None):
    """
    On Job Offer submit:
      - Find Employee where employee.job_applicant == doc.job_applicant
      - Insert & submit Air Ticket Entitlement with mapped fields
    """
    if not getattr(doc, "job_applicant", None):
        frappe.log_error(
            f"Job Offer {doc.name} has no job_applicant set.",
            "Air Ticket Entitlement Hook"
        )
        return

    # Find the Employee linked to this Job Applicant
    employee_name = frappe.db.get_value(
        "Employee",
        {"job_applicant": doc.job_applicant},
        "name"
    )

    if not employee_name:
        frappe.log_error(
            f"No Employee found with job_applicant={doc.job_applicant} for Job Offer {doc.name}",
            "Air Ticket Entitlement Hook"
        )
        return

    # Pull required Employee fields
    date_of_joining = frappe.db.get_value("Employee", employee_name, "date_of_joining")

    # Source values from Job Offer custom fields
    ticket_amount = getattr(doc, "custom_air_ticket_entitlement_cash_amount", None)
    duration_value = getattr(doc, "custom_air_ticket_entitlement_duration", None)


    # Build and insert the entitlement
    entitlement = frappe.get_doc({
        "doctype": "Air Ticket Entitlement",
        "employee": employee_name,
        "employee_onboarding_date": date_of_joining,
        "ticket_amount": ticket_amount,
        "ticket_entitlement_duration": duration_value,
    })

    # Insert and submit (since you asked for a "submitted record")
    entitlement.insert(ignore_permissions=True)
    try:
        entitlement.submit()
    except Exception as e:
        # If submit fails (e.g., workflow), at least log it; record remains inserted (Draft)
        frappe.log_error(f"Failed to submit Air Ticket Entitlement {entitlement.name}: {e}")
