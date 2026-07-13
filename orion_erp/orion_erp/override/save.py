import json

import frappe
from frappe.desk.form.save import run_onload, send_updated_docs, set_local_name
from frappe.model.docstatus import DocStatus
from frappe.monitor import add_data_to_monitor
from frappe.utils.scheduler import is_scheduler_inactive
from frappe.utils.telemetry import capture_doc


@frappe.whitelist(methods=["POST", "PUT"])
def savedocs(doc, action):
	"""save / submit / update doclist"""
	doc = frappe.get_doc(json.loads(doc))
	capture_doc(doc, action)
	if doc.get("__islocal") and doc.name.startswith("new-" + doc.doctype.lower().replace(" ", "-")):
		doc.__temporary_name = doc.name
	set_local_name(doc)

	doc.docstatus = {
		"Save": DocStatus.DRAFT,
		"Submit": DocStatus.SUBMITTED,
		"Update": DocStatus.SUBMITTED,
		"Cancel": DocStatus.CANCELLED,
	}[action]

	if doc.docstatus.is_submitted():
		if action == "Submit" and doc.meta.queue_in_background and not is_scheduler_inactive():
			from frappe.core.doctype.submission_queue.submission_queue import queue_submission

			queue_submission(doc, action)
			return
		if action == "Update":
			current = frappe.db.get_value(doc.doctype, doc.name, "modified")
			if current:
				doc._original_modified = current
				doc.modified = current
			db_doc = frappe.get_doc(doc.doctype, doc.name)
			for fieldname in ("custom_medical_certificate_status",):
				db_val = db_doc.get(fieldname)
				if doc.get(fieldname) != db_val:
					doc.set(fieldname, db_val)
			doc.save(ignore_permissions=True)
		else:
			doc.submit()
	else:
		doc.save()

	run_onload(doc)
	send_updated_docs(doc)

	add_data_to_monitor(doctype=doc.doctype, action=action)
	status_message = "Submitted" if doc.docstatus.is_submitted() else "Saved"
	frappe.msgprint(frappe._(status_message), indicator="green", alert=True)
