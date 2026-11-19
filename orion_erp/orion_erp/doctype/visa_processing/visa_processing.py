
# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, add_months, getdate, today

class VisaProcessing(Document):

    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hrms.hr.doctype.job_offer_term.job_offer_term import JobOfferTerm
        from orion_erp.orion_erp.doctype.confidental_certificates.confidental_certificates import ConfidentalCertificates
        from orion_erp.orion_erp.doctype.employee_cdt.employee_cdt import Employeecdt

        adnoc_medical: DF.Literal["", "Fit to Work", "Remedical - Fit to work", "NA", "Pending", "Unfit", "Remedical"]
        allocation: DF.Data | None
        candidate_name: DF.Data
        certificates: DF.Table[Employeecdt]
        change_status_approval: DF.Literal["Pending", "Approved", "Rejected", "Not Required"]
        change_status_approval_date: DF.Date | None
        contract_signature: DF.Literal["", "Yes", "No"]
        current_passport_location: DF.Literal["", "In", "Out", "With Previous Employer", "Employee"]
        date_of_selection: DF.Date | None
        department: DF.Literal["", "Rental Department", "Tankering Department", "Solid Waste", "Pest Control", "Rental Offshore"]
        documents: DF.Literal["", "Yes", "No"]
        job_applicant: DF.Link
        job_offer_terms: DF.Table[JobOfferTerm]
        job_trade: DF.Literal["", "HEAVY BUS DRIVER", "LIGHT VEHICLE DRIVER"]
        joining_date: DF.Date | None
        joining_status: DF.Data | None
        labour_application: DF.Literal["", "Yes", "No"]
        last_updated_by: DF.Date | None
        medical_insurance: DF.Literal["", "Yes", "No"]
        nationality: DF.Link | None
        notes: DF.SmallText | None
        offer_letter: DF.Literal["", "pending", "Accepted", "Not Issued", "Issued but not Accepted Yet"]
        processing_requirement: DF.Literal["", "Work Permit Only", "Work Permit + Visa Processing"]
        re_medical: DF.SmallText | None
        reason_for_unfit: DF.Data | None
        rejection_reason: DF.SmallText | None
        remarks: DF.SmallText | None
        salary: DF.Data | None
        salary_start_date: DF.Date | None
        sent_to_operations: DF.Check
        site_mobilization: DF.Date | None
        skill_type: DF.Literal["Skilled", "Unskilled"]
        staff_category: DF.Data | None
        status: DF.Literal["", "Approved", "Rejected", "In Progress"]
        status_change: DF.Literal["", "Yes", "No"]
        table_euhb: DF.Table[ConfidentalCertificates]
        temporary_work_permit_applied: DF.Literal["", "Yes", "No"]
        temporary_work_permit_expiry: DF.Literal["6 months", "1 year", "2 year"]
        training_card: DF.Literal["", "Yes", "No", "Pending"]
        visa_application: DF.Literal["", "Yes", "No", "Rejected"]
        visa_cancelled_date: DF.Date | None
        visa_medical: DF.Literal["", "Yes", "No", "Failed"]
        visa_stamping: DF.Literal["", "Yes", "No"]
        visa_status: DF.Literal["", "Visit Visa", "Tourist Visa", "Employment Visa", "Family Visa", "Golden Visa", "Freelance Visa", "Student Visa", "Residence Visa", "Visa Under Process", "Visa Expired", "Cancelled Visa", "Visa Not Available"]
    # end: auto-generated types

    def validate(self):
        self.validate_duplicate_job_applicant()

    def validate_duplicate_job_applicant(self):
        if not self.job_applicant:
            return

        existing = frappe.db.exists(
            "Visa Processing",
            {
                "job_applicant": self.job_applicant,
                "name": ["!=", self.name]
            }
        )

        if existing:
            frappe.throw(
                "Visa Processing already exists for this Job Applicant. "
                "Only one Visa Processing record is allowed."
            )

    def on_update(self):
        sync_from_visa_processing(self)
        # Send once, on the save where status becomes Approved
        if self.status == "Approved" and self.has_value_changed("status"):
            send_visa_completed_mail(self)

        

    def on_update_after_submit(self):
        sync_from_visa_processing(self)

############################### Fine notification ###########################################

    ############################### ICP fine notification (outside the class) ###############################

NOTIFY_USER = ["HR Manager", "HR User"]

def get_hr_emails():
	users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", NOTIFY_USER], "parenttype": "User"},
		pluck="parent",
	)
	if not users:
		return []

	emails = frappe.get_all(
		"User",
		filters={
			"name": ["in", list(set(users))],
			"enabled": 1,
			"user_type": "System User",
			"email": ["is", "set"],
		},
		pluck="email",
	)
	return list(set(emails))


def get_icp_due_date(cancelled_date, skill_type):
    cancelled = getdate(cancelled_date)

    if skill_type == "Skilled":
        return add_months(cancelled, 3)  # 3 months after cancellation

    if skill_type == "Unskilled":
        return add_days(cancelled, 28)  # 28 days after cancellation

    return None


def send_alert(docname, title, body):

    recipients = get_hr_emails()

    if not recipients:
        frappe.throw("No enabled users found with the HR role.")

    # System notification (bell icon)
    frappe.get_doc({
        "doctype": "Notification Log",
        "subject": title,
        "for_user": recipients,
        "type": "Alert",
        "document_type": "Visa Processing",
        "document_name": docname,
        "email_content": body,
    }).insert(ignore_permissions=True)

    # Email
    frappe.sendmail(
        recipients=recipients,
        subject=title,
        message=body,
        now=True
    )


def send_icp_fine_notifications():
    """Daily alert after the ICP grace period ends, until status change is Approved."""
    rows = frappe.get_all(
        "Visa Processing",
        filters={
            "visa_cancelled_date": ["is", "set"],
            "skill_type": ["is", "set"],
        },
        fields=["name", "candidate_name", "skill_type",
                "visa_cancelled_date", "change_status_approval"],
    )

    for r in rows:
        # Stop once approved
        if r.change_status_approval == "Approved":
            continue

        due = get_icp_due_date(r.visa_cancelled_date, r.skill_type)

        # Not due yet
        if not due or due > getdate(today()):
            continue

        title = "ICP Fine Alert: {0}".format(r.candidate_name or r.name)

        body = """
            <p>The ICP grace period has ended for this visa and the status change is not approved yet:</p>
            <ul>
                <li><b>Visa Processing:</b> {0}</li>
                <li><b>Candidate:</b> {1}</li>
                <li><b>Skill Type:</b> {2}</li>
                <li><b>Visa Cancelled On:</b> {3}</li>
                <li><b>Grace Period Ended On:</b> {4}</li>
            </ul>
            <p>Please take action to avoid ICP fines.</p>
        """.format(r.name, r.candidate_name or "", r.skill_type,
                   r.visa_cancelled_date, due)

        send_alert(r.name, title, body)

    frappe.db.commit()


def send_medical_insurance_fine_notifications():
    """Daily alert from the 11th day after the status change approval date,
    until medical_insurance is Yes."""
    rows = frappe.get_all(
        "Visa Processing",
        filters={"change_status_approval_date": ["is", "set"]},
        fields=["name", "candidate_name", "change_status_approval_date",
                "medical_insurance"],
    )

    for r in rows:
        # Stop once medical insurance is done
        if r.medical_insurance == "Yes":
            continue

        due = add_days(getdate(r.change_status_approval_date), 11)

        # Not due yet
        if due > getdate(today()):
            continue

        days_overdue = (getdate(today()) - due).days

        title = "Medical Insurance Fine Alert: {0}".format(r.candidate_name or r.name)

        body = """
            <p>The 11-day period after the status change approval has ended and the medical insurance is not completed:</p>
            <ul>
                <li><b>Visa Processing:</b> {0}</li>
                <li><b>Candidate:</b> {1}</li>
                <li><b>Status Change Approved On:</b> {2}</li>
                <li><b>Medical Insurance Fine Date:</b> {3}</li>
                <li><b>Days Past Fine Date:</b> {4}</li>
            </ul>
            <p>Please complete the medical insurance to avoid a fine.</p>
        """.format(r.name, r.candidate_name or "",
                   r.change_status_approval_date, due, days_overdue)

        send_alert(r.name, title, body)

    frappe.db.commit()


DEPARTMENT_ROLE_MAP = {
    "Rental Department": "Rental Management",
    "Tankering Department": "Tankering Department",
    "Solid Waste": "Solid Waste",
    "Pest Control": "Pest Control",
    "Rental Offshore": "Rental Offshore",
}
 
# Names used in the Certificates table (Certification Name column)
PASSPORT_CERT_NAME = "Passport No"
CHANGE_STATUS_CERT_NAME = "Change Status"
DRIVING_LICENSE = "Driving License"
 
 
def get_role_emails(role):
    """Emails of all enabled users who have the given role."""
    users = frappe.get_all(
        "Has Role",
        filters={"role": role, "parenttype": "User"},
        pluck="parent",
    )
    users = [u for u in set(users) if u not in ("Administrator", "Guest")]
    if not users:
        return []
 
    return frappe.get_all(
        "User",
        filters={"name": ["in", users], "enabled": 1},
        pluck="email",
    )
 
 
def get_cert_row(doc, cert_name):
    """Find a row in the Certificates table by Certification Name."""
    for row in doc.certificates:
        if (row.get("certification_name") or "").strip().lower() == cert_name.lower():
            return row
    frappe.throw("No '{0}' row found in the Certificates table.".format(cert_name))
 
 
def get_row_attachment(row, label):
    """Build a frappe.sendmail attachment dict from a certificates row."""
    if not row.get("attachment"):
        frappe.throw("The '{0}' row has no attachment.".format(label))
 
    file_doc = frappe.get_doc("File", {"file_url": row.attachment})
    return {
        "fname": file_doc.file_name,
        "fcontent": file_doc.get_content(),
    }
 
 
@frappe.whitelist()
def send_to_operations(docname):
    doc = frappe.get_doc("Visa Processing", docname)
    frappe.has_permission("Visa Processing", "write", doc, throw=True)
 
    if doc.change_status_approval != "Approved":
        frappe.throw("Change Status Approval must be Approved before sending.")
 
    # Block a second send
    if doc.get("sent_to_operations"):
        frappe.throw("The details were already sent to Operations.")
 
    # ---- Department -> Role -> Recipients ----
    department = doc.get("department")
    if not department:
        frappe.throw("Department is not set on this Visa Processing record.")
 
    role = DEPARTMENT_ROLE_MAP.get(department)
    if not role:
        frappe.throw("No role is mapped for department {0}.".format(department))
 
    recipients = get_role_emails(role)
    if not recipients:
        frappe.throw("No enabled users found with the role {0}.".format(role))
 
    # ---- Job Applicant details ----
    applicant = frappe.db.get_value(
        "Job Applicant",
        doc.job_applicant,
        ["phone_number", "designation"],
        as_dict=True,
    ) or {}
 
    contact_no = applicant.get("phone_number") or ""
    designation = doc.get("designation") or applicant.get("designation") or ""
 
    # ---- Attachments from the Certificates table ----
    passport_row = get_cert_row(doc, PASSPORT_CERT_NAME)
    change_status_row = get_cert_row(doc, CHANGE_STATUS_CERT_NAME)
    driving_license_row = get_cert_row(doc, DRIVING_LICENSE)
 
    attachments = [
        get_row_attachment(passport_row, PASSPORT_CERT_NAME),
        get_row_attachment(change_status_row, CHANGE_STATUS_CERT_NAME),
        get_row_attachment(driving_license_row,DRIVING_LICENSE )
    ]
 
    frappe.sendmail(
        recipients=recipients,
        subject="Visa Approved: {0}".format(doc.candidate_name),
        message="""
            <p>Dear {0} Team,</p>
            <p>The status change has been approved for the following candidate:</p>
            <ul>
                <li><b>Name:</b> {1}</li>
                <li><b>Designation:</b> {2}</li>
                <li><b>Department:</b> {3}</li>
                <li><b>Contact No:</b> {4}</li>
                <li><b>Passport No:</b> {5}</li>
            </ul>
            <p>The passport copy and change status copy are attached.</p>
        """.format(
            department,
            doc.candidate_name,
            designation,
            department,
            contact_no,
            passport_row.get("reference_no") or "",
        ),
        attachments=attachments,
        reference_doctype="Visa Processing",
        reference_name=doc.name,
        now=True,
    )
 
    doc.db_set("sent_to_operations", 1)
    doc.add_comment(
        "Info",
        "Details sent to {0} role ({1} users)".format(role, len(recipients)),
    )
    return "sent"
 


# ---------------- Visa completion mail (PRO + department) ----------------

# Role name of the PRO users. Change to your exact role name.
PRO_ROLE = "PRO"

# Certification Name values in the Certificates table to attach.
# Matching ignores case and extra spaces. Change to your exact names.
COMPLETION_MAIL_CERTS = [
    "Passport No",
    "Residence Permit",
    "EID copy",
    "Medical Insurance",
    "Labour Card",
    "Picture",
]


def get_completion_attachments(doc):
    """Returns (attachments, missing). Missing files are skipped, not fatal."""
    attachments, missing = [], []

    for cert_name in COMPLETION_MAIL_CERTS:
        row = next(
            (
                r for r in (doc.certificates or [])
                if (r.get("certification_name") or "").strip().lower() == cert_name.lower()
                and r.get("attachment")
            ),
            None,
        )
        if not row:
            missing.append(cert_name)
            continue

        file_name = frappe.db.get_value("File", {"file_url": row.attachment}, "name")
        if not file_name:
            missing.append(cert_name)
            continue

        try:
            file_doc = frappe.get_doc("File", file_name)
            attachments.append({
                "fname": file_doc.file_name,
                "fcontent": file_doc.get_content(),
            })
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Visa completion mail: cannot read " + cert_name)
            missing.append(cert_name)

    return attachments, missing


def send_visa_completed_mail(doc):
    """Visa completed: mail the PRO and the candidate's department."""
    department = doc.get("department")
    dept_role = DEPARTMENT_ROLE_MAP.get(department)

    recipients = set()
    if dept_role:
        recipients.update(get_role_emails(dept_role))
    recipients.update(get_role_emails(PRO_ROLE))
    recipients = sorted(e for e in recipients if e)

    if not recipients:
        frappe.msgprint("Visa completion mail not sent: no PRO or department users found.", indicator="orange")
        return

    attachments, missing = get_completion_attachments(doc)
    if missing:
        frappe.msgprint("Not attached (no file found): {0}".format(", ".join(missing)), indicator="orange")

    applicant = frappe.db.get_value(
        "Job Applicant", doc.job_applicant, ["phone_number", "designation"], as_dict=True
    ) or {}

    try:
        frappe.sendmail(
            recipients=recipients,
            subject="Visa Processing Completed: {0}".format(doc.candidate_name),
            message="""
                <p>Dear PRO and {0} Team,</p>
                <p>The visa processing has been <b>completed</b> for the following candidate:</p>
                <ul>
                    <li><b>Name:</b> {1}</li>
                    <li><b>Designation:</b> {2}</li>
                    <li><b>Department:</b> {3}</li>
                    <li><b>Contact No:</b> {4}</li>
                    <li><b>Visa Status:</b> {5}</li>
                </ul>
                <p>The documents are attached.</p>
            """.format(
                department or "",
                doc.candidate_name,
                doc.get("designation") or applicant.get("designation") or "",
                department or "",
                applicant.get("phone_number") or "",
                doc.get("visa_status") or "",
            ),
            attachments=attachments,
            reference_doctype="Visa Processing",
            reference_name=doc.name,
            now =True
        )
        doc.add_comment("Info", "Visa completion mail sent to PRO and {0}".format(department or "-"))
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Visa completion mail failed")




# Statuses that stop the daily one-month alert
ONE_MONTH_ALERT_STOP_STATUSES = ["Approved", "Rejected"]


def send_visa_one_month_notifications():
    """Daily system notification to HR for every Visa Processing that is
    more than one month old and not yet Approved/Rejected."""
    recipients = get_hr_emails()
    if not recipients:
        return  # nothing to do; don't throw inside a scheduled job

    # Created on or before the same date one month ago
    cutoff = add_days(add_months(getdate(today()), -1), 1)

    rows = frappe.get_all(
        "Visa Processing",
        filters={
            "creation": ["<", cutoff],
            "status": ["not in", ONE_MONTH_ALERT_STOP_STATUSES],
        },
        fields=["name", "candidate_name", "creation", "status"],
    )

    for r in rows:
        days_open = (getdate(today()) - getdate(r.creation)).days

        title = "Visa Over One Month: {0}".format(r.candidate_name or r.name)
        body = """
            <p>This visa processing has been open for more than one month and is not completed yet:</p>
            <ul>
                <li><b>Visa Processing:</b> {0}</li>
                <li><b>Candidate:</b> {1}</li>
                <li><b>Created On:</b> {2}</li>
                <li><b>Days Open:</b> {3}</li>
                <li><b>Status:</b> {4}</li>
            </ul>
        """.format(r.name, r.candidate_name or "", getdate(r.creation),
                   days_open, r.status or "Not set")

        for user in recipients:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": title,
                "for_user": user,
                "type": "Alert",
                "document_type": "Visa Processing",
                "document_name": r.name,
                "email_content": body,
            }).insert(ignore_permissions=True)

    frappe.db.commit()



def sync_from_visa_processing(doc, method=None):
    """Runs on every save of a Visa Processing record. Pushes its certificates
    into the Pre-Employment Training of the same Job Applicant, even if that
    training is already saved/approved."""
    if not doc.get("job_applicant"):
        return

    pet_name = frappe.db.get_value(
        "Pre-Employment Training",
        {"job_applicant": doc.job_applicant, "docstatus": ["!=", 2]},
        "name",
    )
    if not pet_name:
        return

    child_dt = frappe.get_meta("Pre-Employment Training").get_field("documents").options

    existing = {}
    for r in frappe.get_all(
        child_dt,
        filters={
            "parent": pet_name,
            "parenttype": "Pre-Employment Training",
            "parentfield": "documents",
        },
        fields=["name", "name1", "idx", "issued_date", "expiry_date", "attachment"],
    ):
        existing[(r.name1 or "").strip().lower()] = r

    next_idx = max([r.idx for r in existing.values()] or [0]) + 1

    # Visa Processing field -> Pre-Employment Training field
    field_map = {
        "date_of_issue": "issued_date",
        "date_of_expiry": "expiry_date",
        "attachment": "attachment",
    }

    changed = []
    for cert in doc.certificates:
        key = (cert.certification_name or "").strip().lower()
        if not key:
            continue

        values = {tgt: cert.get(src) for src, tgt in field_map.items() if cert.get(src)}
        row = existing.get(key)

        if row:
            # update only what is new or different, never overwrite with blanks
            updates = {k: v for k, v in values.items() if row.get(k) != v}
            if updates:
                frappe.db.set_value(child_dt, row.name, updates, update_modified=False)
                changed.append(cert.certification_name)
        else:
            frappe.get_doc({
                "doctype": child_dt,
                "parent": pet_name,
                "parenttype": "Pre-Employment Training",
                "parentfield": "documents",
                "idx": next_idx,
                "name1": cert.certification_name,
                **values,
            }).insert(ignore_permissions=True)
            next_idx += 1
            changed.append(cert.certification_name)

    if changed:
        pet = frappe.get_doc("Pre-Employment Training", pet_name)
        pet.add_comment(
            "Info",
            "Synced from Visa Processing {0}: {1}".format(doc.name, ", ".join(changed)),
        )
        pet.notify_update()  # refreshes the form if someone has it open