"""Keep explicitly identified medical certificates in sync after leave approval."""

import frappe
from frappe import _

FIELD = "custom_medical_certificate"
STATUS = "custom_medical_certificate_status"


def _required(leave_type):
    return bool(frappe.db.get_value("Leave Type", leave_type,
                                  "custom_medical_certificate_required"))


def _linked_application(file):
    if (file.attached_to_doctype != "Leave Application"
            or file.attached_to_field != FIELD or not file.attached_to_name
            or not frappe.db.exists("Leave Application", file.attached_to_name)):
        return None
    return frappe.get_doc("Leave Application", file.attached_to_name)


def update_medical_certificate_status_on_file_attach(file, method=None):
    doc = _linked_application(file)
    if not doc or doc.docstatus == 2 or not file.file_url:
        return
    # An S3 uploader can replace the URL after insertion. Always use its final
    # URL, even when the certificate status was already Submitted.
    frappe.db.set_value("Leave Application", doc.name, {
        FIELD: file.file_url, STATUS: "Submitted" if _required(doc.leave_type) else "",
    }, update_modified=False)
    doc.notify_update()


def reset_medical_certificate_status_on_file_trash(file, method=None):
    doc = _linked_application(file)
    if not doc or doc.docstatus == 2 or doc.get(FIELD) != file.file_url:
        return
    # Removing an older attachment must not clear a newer certificate, and a
    # duplicate File record still supporting the same URL remains valid.
    if frappe.db.exists("File", {"attached_to_doctype": "Leave Application",
            "attached_to_name": doc.name, "attached_to_field": FIELD,
            "file_url": file.file_url, "name": ["!=", file.name]}):
        return
    frappe.db.set_value("Leave Application", doc.name, {
        FIELD: "", STATUS: "Pending" if _required(doc.leave_type) else "",
    }, update_modified=False)
    doc.notify_update()


@frappe.whitelist()
def select_medical_certificate(application, file_name):
    """Explicitly identify an existing attachment; never infer from its name."""
    doc = frappe.get_doc("Leave Application", application)
    doc.check_permission("write")
    if doc.docstatus == 2:
        frappe.throw(_("A cancelled application cannot be changed."))
    if not _required(doc.leave_type):
        frappe.throw(_("This leave type does not require a medical certificate."))
    file = frappe.get_doc("File", file_name)
    file.check_permission("read")
    if (file.attached_to_doctype != "Leave Application"
            or file.attached_to_name != doc.name
            or file.attached_to_field not in (None, "", FIELD)
            or not file.file_url):
        frappe.throw(_("Select a file attached to this application's Medical Certificate field or general attachments."))
    file.check_permission("write")
    file.attached_to_field = FIELD
    file.save()
    # Preserve the application status, workflow, dates, balance and ledger.
    update_medical_certificate_status_on_file_attach(file)
    doc.add_comment("Info", _("An existing attachment was selected as the Medical Certificate."))
    return {FIELD: file.file_url, STATUS: "Submitted"}
