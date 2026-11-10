# import frappe

# def create_air_ticket_entitlement_on_submit(doc, method=None):
#     """
#     On Job Offer submit:
#       - Find Employee where employee.job_applicant == doc.job_applicant
#       - Insert & submit Air Ticket Entitlement with mapped fields
#     """
#     if not getattr(doc, "job_applicant", None):
#         frappe.log_error(
#             f"Job Offer {doc.name} has no job_applicant set.",
#             "Air Ticket Entitlement Hook"
#         )
#         return

#     # Find the Employee linked to this Job Applicant
#     employee_name = frappe.db.get_value(
#         "Employee",
#         {"job_applicant": doc.job_applicant},
#         "name"
#     )

#     if not employee_name:
#         frappe.log_error(
#             f"No Employee found with job_applicant={doc.job_applicant} for Job Offer {doc.name}",
#             "Air Ticket Entitlement Hook"
#         )
#         return

#     # Pull required Employee fields
#     date_of_joining = frappe.db.get_value("Employee", employee_name, "date_of_joining")

#     # Source values from Job Offer custom fields
#     ticket_amount = getattr(doc, "custom_air_ticket_entitlement_cash_amount", None)
#     duration_value = getattr(doc, "custom_air_ticket_entitlement_duration", None)


#     # Build and insert the entitlement
#     entitlement = frappe.get_doc({
#         "doctype": "Air Ticket Entitlement",
#         "employee": employee_name,
#         "employee_onboarding_date": date_of_joining,
#         "ticket_amount": ticket_amount,
#         "ticket_entitlement_duration": duration_value,
#     })

#     # Insert and submit (since you asked for a "submitted record")
#     entitlement.insert(ignore_permissions=True)
#     try:
#         entitlement.submit()
#     except Exception as e:
#         # If submit fails (e.g., workflow), at least log it; record remains inserted (Draft)
#         frappe.log_error(f"Failed to submit Air Ticket Entitlement {entitlement.name}: {e}")




import frappe
from frappe import _
from frappe.utils import get_url_to_form


DOCTYPE = "Job Offer"

# Workflow states
DRAFT = "Draft"
PENDING_HR = "Pending HR Approval"
PENDING_DEPARTMENT = "Pending Department Approval"
AWAITING_HR_ACCEPTANCE = "Awaiting HR Acceptance"
PENDING_HR_REVERIFICATION = "Pending HR Re-Verification"
PENDING_GM = "Pending GM Approval"
APPROVED = "Approved"
REJECTED = "Rejected"


def get_workflow_recipients(doc, state):
    """
    Return the users who should receive notification
    for the newly entered workflow state.
    """

    users = []

    # HR Manager approval
    if state == PENDING_HR:
        users = frappe.get_all(
            "Has Role",
            filters={
                "role": "HR Manager",
                "parenttype": "User"
            },
            pluck="parent"
        )

    # Selected Department Manager
    elif state == PENDING_DEPARTMENT:

        manager = doc.custom_department_manager

        if manager:
            users = [manager]

    # HR User acceptance
    elif state == AWAITING_HR_ACCEPTANCE:
        users = frappe.get_all(
            "Has Role",
            filters={
                "role": "HR User",
                "parenttype": "User"
            },
            pluck="parent"
        )

    # HR Manager re-verification
    elif state == PENDING_HR_REVERIFICATION:
        users = frappe.get_all(
            "Has Role",
            filters={
                "role": "HR Manager",
                "parenttype": "User"
            },
            pluck="parent"
        )

    # General Manager approval
    elif state == PENDING_GM:
        users = frappe.get_all(
            "Has Role",
            filters={
                "role": "General Manager",
                "parenttype": "User"
            },
            pluck="parent"
        )

    # Final result: notify applicant
    elif state in (APPROVED, REJECTED):
        if doc.owner:
            users = [doc.owner]

    # Remove duplicates, disabled users and Administrator
    recipients = []

    for user in set(users):

        if not user or user == "Administrator":
            continue

        enabled = frappe.db.get_value(
            "User", user, "enabled"
        )

        if enabled:
            recipients.append(user)

    return recipients


def send_job_offer_notification(doc, user, state):
    """
    Send both system notification and email.
    """

    state_messages = {
        PENDING_HR: "A Job Offer requires your HR approval.",
        PENDING_DEPARTMENT: "A Job Offer requires your Department approval.",
        AWAITING_HR_ACCEPTANCE: "A Job Offer is waiting for HR acceptance.",
        PENDING_HR_REVERIFICATION: "A Job Offer requires HR re-verification.",
        PENDING_GM: "A Job Offer requires your final approval.",
        APPROVED: "The Job Offer has been approved.",
        REJECTED: "The Job Offer has been rejected."
    }

    message = state_messages.get(state)

    if not message:
        return

    user_email = frappe.db.get_value(
        "User", user, "email"
    )

    frappe.log_error(
    title="Job Offer Email Debug",
    message=f"User: {user}\nEmail: {user_email}"
)

    subject = f"Job Offer Workflow - {state}"

    document_url = get_url_to_form(
        DOCTYPE, doc.name
    )

    email_message = f"""
        <p>Hello,</p>

        <p>{message}</p>

        <p>
            <b>Job Offer:</b> {frappe.utils.escape_html(doc.name)}<br>
            <b>Department:</b> {frappe.utils.escape_html(doc.custom_department or "")}<br>
            <b>Staff Category:</b> {frappe.utils.escape_html(doc.custom_staff_category or "")}<br>
            <b>Current Stage:</b> {frappe.utils.escape_html(state)}
        </p>

        <p>
            <a href="{document_url}">Open Job Offer</a>
        </p>

        <p>Thank you.</p>
    """

    # 1. Create system notification
    try:
        notification = frappe.get_doc({
            "doctype": "Notification Log",
            "for_user": user,
            "from_user": frappe.session.user,
            "type": "Alert",
            "document_type": DOCTYPE,
            "document_name": doc.name,
            "subject": subject,
            "email_content": message
        })

        notification.insert(ignore_permissions=True)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Job Offer System Notification Error"
        )

    # 2. Send email separately
    if user_email:

        try:
            frappe.sendmail(
                recipients=[user_email],
                subject=subject,
                message=email_message,
                reference_doctype=DOCTYPE,
                reference_name=doc.name,
                now = True
            )

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "Job Offer Email Notification Error"
            )


def notify_job_offer_workflow_change(doc, method=None):
    """
    Send notifications only when workflow state changes.
    """

    if doc.doctype != DOCTYPE:
        return

    old_doc = doc.get_doc_before_save()

    if not old_doc:
        return

    old_state = old_doc.get("workflow_state")
    new_state = doc.get("workflow_state")

    # Do not send notifications for normal field updates.
    if old_state == new_state:
        return

    recipients = get_workflow_recipients(
        doc, new_state
    )

    for user in recipients:

        send_job_offer_notification(
            doc,
            user,
            new_state
        )

def job_offer_on_update(doc, method=None):

    # New system and email notifications
    notify_job_offer_workflow_change(doc, method)



def validate_job_offer_workflow(doc, method=None):
    """Validate Job Offer rejection and record the rejecting user."""

    if doc.doctype != DOCTYPE:
        return

    old_doc = doc.get_doc_before_save()

    if not old_doc:
        return

    old_state = old_doc.get("workflow_state")
    new_state = doc.get("workflow_state")

    # When the Job Offer is rejected
    if new_state == REJECTED and old_state != REJECTED:

        # Rejection reason is mandatory
        if not doc.custom_rejection_reason:
            frappe.throw(
                _("Please enter the Rejection Reason before rejecting this Job Offer.")
            )

        # Automatically record the logged-in user
        doc.custom_rejected_by = frappe.session.user

