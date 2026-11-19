# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import formatdate
from frappe import _
from frappe.utils import get_link_to_form

MANDATORY_TRAININGS = [
    "Basic First Aid",
    "Basic Fire Fighting",
    "Fire Safety",
    "H2S Awareness and Escape Level II",
    "Onshore HSE Induction + ADNOC Life Saving Rules",
    "Defensive/Desert Driving (DDC)",
    "ADNOC Document For Safe Driving (ADSD)",
]

class PreEmploymentTraining(Document):

    def validate(self):
        self.validate_duplicate_job_applicant()
        self.validate_mandatory_trainings()

	

	
    def validate_duplicate_job_applicant(self):
        if not self.job_applicant:
            return

        existing = frappe.db.get_value(
            "Pre-Employment Training",
            {
                "job_applicant": self.job_applicant,
                "name": ["!=", self.name],
                "docstatus": ["!=", 2],
            },
            "name",
        )
        if existing:
            frappe.throw(
                _("Pre-Employment Training {0} already exists for Job Applicant {1}. Only one is allowed per applicant.").format(
                    get_link_to_form("Pre-Employment Training", existing),
                    frappe.bold(self.job_applicant),
                ),
                title=_("Duplicate Pre-Employment Training"),
            )
    def validate_mandatory_trainings(self):
        rows = {(d.name1 or "").strip().lower(): d for d in self.documents}

        missing_rows = [t for t in MANDATORY_TRAININGS if t.lower() not in rows]
        missing_files = [
            t for t in MANDATORY_TRAININGS
            if t.lower() in rows and not rows[t.lower()].attachment
        ]

        if missing_rows:
            frappe.throw(
                _("Missing mandatory trainings:<br>") + "<br>".join(missing_rows),
                title=_("Mandatory Trainings"),
            )
        if missing_files:
            frappe.throw(
                _("Attachment is required for:<br>") + "<br>".join(missing_files),
                title=_("Mandatory Trainings"),
            )
	

HR_ROLES = ["HR Manager", "HR User"]


def get_hr_emails():
	users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", HR_ROLES], "parenttype": "User"},
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


@frappe.whitelist()
def send_to_hr(docname):
	doc = frappe.get_doc("Pre-Employment Training", docname)
	frappe.has_permission("Pre-Employment Training", "write", doc, throw=True)

	if doc.status != "Completed":
		frappe.throw("Status must be Completed before sending.")

	if doc.get("sent_to_hr"):
		frappe.throw("This was already sent to HR.")

	recipients = get_hr_emails()
	if not recipients:
		frappe.throw("No enabled users found with the HR role.")

	salary_start = formatdate(doc.salary_start_date) if doc.salary_start_date else ""

	frappe.sendmail(
		recipients=recipients,
		subject="Training Completed: {0}".format(doc.job_applicant_name or doc.job_applicant),
		message="""
			<p>Dear HR Team,</p>
			<p>This person's training is completed. The salary start date is {0}.</p>
			<ul>
				<li><b>Name:</b> {1}</li>
				<li><b>Contact No:</b> {2}</li>
				<li><b>Salary Start Date:</b> {0}</li>
			</ul>
		""".format(salary_start, doc.job_applicant_name or "", doc.phone_number or ""),
		reference_doctype="Pre-Employment Training",
		reference_name=doc.name,
		now=True,
	)

	doc.db_set("sent_to_hr", 1)
	doc.add_comment("Info", "Training completed mail sent to HR ({0} users)".format(len(recipients)))
	return "sent"


