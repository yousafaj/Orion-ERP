import frappe
from frappe import _


# Normalized lookup to keep user-friendly display names in messages
# REQUIRED_CERTS_DISPLAY = ["Passport no", "Emirates ID", "Residence Permit", "Work Permit"]
REQUIRED_CERTS_DISPLAY = ["Passport no"]
REQUIRED_CERTS_MAP = {c.strip().lower(): c for c in REQUIRED_CERTS_DISPLAY}
REQUIRED_CERTS_NORMALIZED = set(REQUIRED_CERTS_MAP.keys())

def _normalize(s: str) -> str:
    return (s or "").strip().lower()


def validate_employee(doc, method):
    _validate_required_certificates(doc)
    sync_existing_certificates(doc)
    create_air_ticket_entitlement_from_employee(doc)

def _validate_required_certificates(doc):
    """
    Build a set of certification_name values from the child table and verify
    that it includes: Passport no, Emirates ID, Residence Permit, Work Permit.
    """
    present = {
        _normalize(row.certification_name)
        for row in getattr(doc, "custom_certificates", [])
        if getattr(row, "certification_name", None)
    }

    missing_norm = [req for req in REQUIRED_CERTS_NORMALIZED if req not in present]
    if missing_norm:
        # Convert back to their display-cased names
        missing_display = [REQUIRED_CERTS_MAP[m] for m in missing_norm]
        frappe.throw(
            _("Missing required certificates: {0}").format(", ".join(missing_display)),
            title=_("Incomplete Certificates Error")
        )
        
        
def sync_existing_certificates(doc):
    for row in getattr(doc, "custom_certificates", []):
        existing = frappe.get_all(
            "Existing Certificates",
            filters={
                "employee": doc.name,
                "certificate_name": row.certification_name,
                "reference_no": row.reference_no
            },
            fields=["name", "date_of_expiry"]
        )

        if existing:
            existing_cert = existing[0]
            if str(existing_cert.date_of_expiry) != str(row.date_of_expiry):
                frappe.db.set_value("Existing Certificates", existing_cert.name, "date_of_expiry", row.date_of_expiry)
        else:
            frappe.get_doc({
                "doctype": "Existing Certificates",
                "employee": doc.name,
                "certificate_name": row.certification_name,
                "reference_no": row.reference_no,
                "date_of_issue": row.date_of_issue,
                "date_of_expiry": row.date_of_expiry,
                "row_name": row.name
            }).insert(ignore_permissions=True)

def create_air_ticket_entitlement_from_employee(doc, method=None):
    """
    On Employee validate:
      - Find latest submitted Job Offer where job_applicant == employee.job_applicant
      - Create & submit Air Ticket Entitlement for this employee
        * employee_onboarding_date  = employee.date_of_joining
        * ticket_amount             = job_offer.custom_air_ticket_entitlement_cash_amount
        * ticket_entitlement_duration = job_offer.custom_air_ticket_entitlement_duration
    """
    # Need a linked Job Applicant to resolve the Job Offer
    job_applicant = getattr(doc, "job_applicant", None)
    if not job_applicant:
        frappe.msgprint(
            _("Ticket entitlement not created as Job Applicant is not mapped."),
            alert=True,
            indicator="orange",
            title=_("Air Ticket Entitlement")
        )
        return

    # Prefer a submitted Job Offer; fall back to latest if none submitted
    job_offer = frappe.get_all(
        "Job Offer",
        filters={"job_applicant": job_applicant, "docstatus": 1},
        fields=["name", "custom_air_ticket_entitlement_cash_amount", "custom_air_ticket_entitlement_duration"],
        order_by="creation desc",
        limit=1,
    )
    if not job_offer:
        job_offer = frappe.get_all(
            "Job Offer",
            filters={"job_applicant": job_applicant},
            fields=["name", "custom_air_ticket_entitlement_cash_amount", "custom_air_ticket_entitlement_duration", "docstatus"],
            order_by="creation desc",
            limit=1,
        )
    if not job_offer:
        frappe.log_error(f"No Job Offer found for Employee {doc.name} (job_applicant={job_applicant})",
                         "Air Ticket Entitlement (Employee.validate)")
        return

    jo = job_offer[0]
    ticket_amount = jo.get("custom_air_ticket_entitlement_cash_amount")
    duration_value = jo.get("custom_air_ticket_entitlement_duration")

    # If neither value exists on Job Offer, skip quietly
    if ticket_amount is None and duration_value in (None, ""):
        return

    # Upsert entitlement: if one exists for this employee, silent return
    ent_name = frappe.db.get_value("Air Ticket Entitlement", {"employee": doc.name}, "name")
    if ent_name:
        return

    # Create new entitlement
    entitlement = frappe.get_doc({
        "doctype": "Air Ticket Entitlement",
        "employee": doc.name,
        "employee_onboarding_date": doc.date_of_joining,
        "ticket_amount": ticket_amount,
        "ticket_entitlement_duration": duration_value,
    })
    entitlement.insert(ignore_permissions=True)
    try:
        entitlement.submit()
    except Exception as e:
        frappe.log_error(f"Failed to submit Air Ticket Entitlement {entitlement.name}: {e}",
                         "Air Ticket Entitlement (Employee.validate)")
