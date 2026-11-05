# # Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document


# class VisaProcessing(Document):
# 	# begin: auto-generated types
# 	# This code is auto-generated. Do not modify anything in this block.

# 	from typing import TYPE_CHECKING

# 	if TYPE_CHECKING:
# 		from frappe.types import DF

# 		adnoc_medical: DF.Literal["", "Fit to Work", "Remedical - Fit to work", "NA", "Pending"]
# 		allocation: DF.Data | None
# 		candidate_name: DF.Data
# 		contract_signature: DF.Literal["", "Yes", "No"]
# 		date_of_selection: DF.Date | None
# 		documents: DF.Literal["", "Yes", "No"]
# 		job_applicant: DF.Link
# 		job_trade: DF.Literal["", "HEAVY BUS DRIVER", "LIGHT VEHICLE DRIVER"]
# 		joining_date: DF.Date | None
# 		joining_status: DF.Data | None
# 		labour_application: DF.Literal["", "Yes", "No"]
# 		last_updated_by: DF.Date | None
# 		medical_insurance: DF.Literal["", "Yes", "No"]
# 		nationality: DF.Link | None
# 		offer_letter: DF.Literal["", "pending", "Accepted", "Not Issued", "Issued but not Accepted Yet"]
# 		remarks: DF.SmallText | None
# 		salary: DF.Data | None
# 		site_mobilization: DF.Date | None
# 		status_change: DF.Literal["", "Yes", "No"]
# 		tawjeeh: DF.Literal["", "Yes", "No"]
# 		training_card: DF.Literal["", "Yes", "No", "Pending"]
# 		visa_application: DF.Literal["", "Yes", "No"]
# 		visa_medical: DF.Literal["", "Yes", "No"]
# 		visa_stamping: DF.Literal["", "Yes", "No"]



# 	# end: auto-generated types



# 	def validate(self):
#         self.validate_duplicate_job_applicant()

#     def validate_duplicate_job_applicant(self):
#         if not self.job_applicant:
#             return

#         existing = frappe.db.exists(
#             "Visa Processing",
#             {
#                 "job_applicant": self.job_applicant,
#                 "name": ["!=", self.name]
#             }
#         )

#         if existing:
#             frappe.throw(
#                 "Visa Processing already exists for this Job Applicant. "
#                 "Only one Visa Processing record is allowed."
#             )
	



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
        reason_for_unfit: DF.Data | None
        rejection_reason: DF.SmallText | None
        remarks: DF.SmallText | None
        salary: DF.Data | None
        salary_start_date: DF.Date | None
        site_mobilization: DF.Date | None
        skill_type: DF.Literal["Skilled", "Unskilled"]
        status: DF.Literal["", "Approved", "Rejected", "In Progress"]
        status_change: DF.Literal["", "Yes", "No"]
        temporary_work_permit_applied: DF.Literal["", "Yes", "No"]
        temporary_work_permit_expiry: DF.Literal["6 months", "1 year", "2 year"]
        training_card: DF.Literal["", "Yes", "No", "Pending"]
        visa_application: DF.Literal["", "Yes", "No", "Rejected"]
        visa_cancelled_date: DF.Date
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


############################### Fine notification ###########################################

    ############################### ICP fine notification (outside the class) ###############################

NOTIFY_USER = "faisal@oriongroup.ae"


def get_icp_due_date(cancelled_date, skill_type):
    cancelled = getdate(cancelled_date)

    if skill_type == "Skilled":
        return add_months(cancelled, 3)   # 3 months after cancellation
    if skill_type == "Unskilled":
        return add_days(cancelled, 28)    # 28 days after cancellation
    return None


def send_alert(docname, title, body):
    # System notification (bell icon)
    frappe.get_doc({
        "doctype": "Notification Log",
        "subject": title,
        "for_user": NOTIFY_USER,
        "type": "Alert",
        "document_type": "Visa Processing",
        "document_name": docname,
        "email_content": body,
    }).insert(ignore_permissions=True)

    # Email (delete this block if you only want the bell notification)
    frappe.sendmail(
        recipients=[NOTIFY_USER],
        subject=title,
        message=body,
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