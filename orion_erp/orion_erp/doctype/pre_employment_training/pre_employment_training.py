# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import formatdate


class PreEmploymentTraining(Document):
	pass

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