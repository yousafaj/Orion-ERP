import frappe
from frappe import _
from frappe.utils import now_datetime


APPROVAL_FLOW = [
    {
        "approver_field": "custom_rejoining_approver_1",
        "status_field": "custom_status_rejoining_approver1"
    },
    {
        "approver_field": "custom_rejoining_approver_2",
        "status_field": "custom_status_rejoining_approver2"
    },
    {
        "approver_field": "custom_rejoining_approver_3",
        "status_field": "custom_status_rejoining_approver3"
    },
    {
        "approver_field": "custom_rejoining_approver_4",
        "status_field": "custom_status_rejoining_approver4"
    },
    {
        "approver_field": "custom_rejoining_approver_5",
        "status_field": "custom_status_rejoining_approver5"
    }
]


def validate_rejoining_approval(doc, method=None):
    current_user = frappe.session.user
    if current_user == "Administrator":
        return

    old_doc = doc.get_doc_before_save()

    if not old_doc:
        if not doc.custom_last_status_change:
            doc.custom_last_status_change = now_datetime()
        if not doc.custom_rejoining_approval_status:
            doc.custom_rejoining_approval_status = "Open"
        return

    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        status_field = row["status_field"]
        old_value = old_doc.get(status_field)
        new_value = doc.get(status_field)

        if old_value != new_value:
            if approver != current_user:
                frappe.throw(
                    _("You are not allowed to update {0}").format(status_field)
                )


def handle_rejoining_approval(doc, method=None):
    old_doc = doc.get_doc_before_save()
    status_changed = False

    if old_doc:
        for row in APPROVAL_FLOW:
            status_field = row["status_field"]
            if old_doc.get(status_field) != doc.get(status_field):
                status_changed = True
                break
        if status_changed:
            doc.db_set("custom_last_status_change", now_datetime())

    statuses = []
    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        status = doc.get(row["status_field"])
        if approver:
            statuses.append(status)

    if "Rejected" in statuses:
        if doc.docstatus != 0:
            frappe.db.set_value(doc.doctype, doc.name, "docstatus", 0)
        update_rejoining_status(doc)
        _notify_rejected(doc, old_doc)
        return

    if "Cancelled" in statuses:
        if doc.docstatus != 2:
            frappe.db.set_value(doc.doctype, doc.name, "docstatus", 2)
        doc.db_set("custom_last_status_change", now_datetime())
        for row in APPROVAL_FLOW:
            if doc.get(row["approver_field"]):
                doc.db_set(row["status_field"], "Cancelled")
        doc.db_set("custom_rejoining_approval_status", "Cancelled")
        _notify_cancelled(doc, old_doc)
        return

    if not statuses:
        doc.db_set("custom_rejoining_approval_status", "Open")
        return

    all_approved = all(status == "Approved" for status in statuses)

    if all_approved:
        _notify_approved(doc, old_doc)
        update_rejoining_status(doc)
        if doc.docstatus != 1:
            doc.flags.ignore_permissions = True
            frappe.flags.ignore_permissions = True
            doc.submit()
        return

    if not old_doc:
        _notify_first_approver(doc)
        update_rejoining_status(doc)
        return

    if status_changed:
        send_next_approval_email(doc)

    update_rejoining_status(doc)


def send_next_approval_email(doc):
    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return

    for index, row in enumerate(APPROVAL_FLOW):
        status_field = row["status_field"]
        old_status = old_doc.get(status_field)
        new_status = doc.get(status_field)

        if old_status != "Approved" and new_status == "Approved":
            next_index = index + 1
            next_approver = None
            while next_index < len(APPROVAL_FLOW):
                next_row = APPROVAL_FLOW[next_index]
                next_approver = doc.get(next_row["approver_field"])
                if next_approver:
                    break
                next_index += 1

            if not next_approver:
                return

            subject = "Rejoining Form Approval Notification"
            link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
            message = f"""
            <h1>Rejoining Form Notification</h1>
            <h3>Details:</h3>
            <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Employee</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Leave Type</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Status</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Open</td>
                </tr>
            </table>
            <br><br>
            <a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">Open Now</a>
            """
            frappe.sendmail(recipients=[next_approver], subject=subject, message=message, now=False)
            return


def update_rejoining_status(doc):
    active_flow = []
    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        status = doc.get(row["status_field"])
        if approver:
            active_flow.append({"approver_field": row["approver_field"], "status": status})

    for row in active_flow:
        if row["status"] == "Rejected":
            doc.db_set("custom_rejoining_approval_status", "Rejected")
            return

    for row in active_flow:
        if row["status"] == "Cancelled":
            doc.db_set("custom_rejoining_approval_status", "Cancelled")
            return

    last_approved = None
    for row in active_flow:
        if row["status"] == "Approved":
            last_approved = row["approver_field"]
        else:
            break

    all_approved = all(row["status"] == "Approved" for row in active_flow)
    if all_approved:
        doc.db_set("custom_rejoining_approval_status", "Submit Pending")
        return

    if last_approved:
        for idx, row in enumerate(active_flow):
            if row["status"] != "Approved":
                doc.db_set("custom_rejoining_approval_status", f"Pending Approval from Approver {idx + 1}")
                return

    doc.db_set("custom_rejoining_approval_status", "Pending Approval from Approver 1")


@frappe.whitelist()
def get_employee_details(employee):
    data = frappe.get_all(
        "Employee",
        filters={"name": employee},
        fields=[
            "employee_name",
            "company",
            "department",
            "designation",
            "user_id",
            "leave_approver",
            "custom_leave_approver_1",
            "custom_leave_approver_2",
            "custom_leave_approver_3",
            "custom_leave_approver_4"
        ],
        limit=1
    )
    if data:
        return data[0]
    return {}


def _notify_first_approver(doc):
    """Send email to the first approver when a new rejoining form is created."""
    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        if approver:
            link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
            subject = _("New Rejoining Form Approval Request - {0}").format(doc.name)
            message = f"""
            <h1>Rejoining Form Notification</h1>
            <h3>Details:</h3>
            <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Employee</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Leave Type</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Status</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Open</td>
                </tr>
            </table>
            <br><br>
            <a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">Open Now</a>
            """
            frappe.sendmail(recipients=[approver], subject=subject, message=message, now=False)
            return


def _notify_approved(doc, old_doc):
    if not old_doc:
        return
    old_statuses = [old_doc.get(row["status_field"]) for row in APPROVAL_FLOW if doc.get(row["approver_field"])]
    if all(s == "Approved" for s in old_statuses):
        return
    employee_email = doc.get("custom_employee_user_id")
    if not employee_email:
        return
    link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
    subject = _("Rejoining Form Approved - {0}").format(doc.name)
    message = f"""
    <h3>Rejoining Form Approved</h3>
    <p>Your rejoining form <b>{doc.name}</b> has been approved by all approvers.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Employee</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Approved</td></tr>
    </table>
    <br><a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Form</a>
    """
    frappe.sendmail(recipients=[employee_email], subject=subject, message=message, now=False)


def _notify_rejected(doc, old_doc):
    if not old_doc:
        return
    was_rejected = any(old_doc.get(row["status_field"]) == "Rejected" for row in APPROVAL_FLOW if doc.get(row["approver_field"]))
    if was_rejected:
        return
    employee_email = doc.get("custom_employee_user_id")
    if not employee_email:
        return
    link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
    subject = _("Rejoining Form Rejected - {0}").format(doc.name)
    message = f"""
    <h3>Rejoining Form Rejected</h3>
    <p>Your rejoining form <b>{doc.name}</b> has been rejected.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Employee</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Rejected</td></tr>
    </table>
    <br><a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Form</a>
    """
    frappe.sendmail(recipients=[employee_email], subject=subject, message=message, now=False)


def _notify_cancelled(doc, old_doc):
    if not old_doc:
        return
    was_cancelled = any(old_doc.get(row["status_field"]) == "Cancelled" for row in APPROVAL_FLOW if doc.get(row["approver_field"]))
    if was_cancelled:
        return

    recipients = set()
    employee_email = doc.get("custom_employee_user_id")
    if employee_email:
        recipients.add(employee_email)

    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        if approver:
            recipients.add(approver)

    hr_roles = frappe.get_all("Role Details", filters={"parent": "Orion Settings", "parentfield": "default_escalation_roles"}, pluck="role")
    if hr_roles:
        hr_users = frappe.get_all("Has Role", filters={"role": ["in", hr_roles], "parenttype": "User"}, pluck="parent")
        for u in hr_users:
            recipients.add(u)

    if not recipients:
        return

    recipients = {r for r in recipients if frappe.utils.validate_email_address(r, throw=False)}
    if not recipients:
        return

    link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
    subject = _("Rejoining Form Cancelled - {0}").format(doc.name)
    message = f"""
    <h3>Rejoining Form Cancelled</h3>
    <p>Rejoining form <b>{doc.name}</b> has been cancelled.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Employee</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Cancelled</td></tr>
    </table>
    <br><a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Form</a>
    """
    frappe.sendmail(recipients=list(recipients), subject=subject, message=message, now=False)


def on_submit_rejoining_form(doc, method=None):
    doc.db_set("custom_rejoining_approval_status", "Approved")


def on_cancel_rejoining_form(doc, method=None):
    doc.db_set("custom_rejoining_approval_status", "Cancelled")


def reset_status_on_amend(doc, method=None):
    if not doc.amended_from:
        return
    if doc.get_doc_before_save():
        return

    for row in APPROVAL_FLOW:
        doc.set(row["status_field"], "Open")
    doc.custom_rejoining_approval_status = "Open"
    doc.custom_last_status_change = now_datetime()


@frappe.whitelist()
def cancel_draft_rejoining(docname):
    doc = frappe.get_doc("Rejoining Form", docname)

    if doc.docstatus != 0:
        frappe.throw(_("Only draft rejoining forms can be cancelled."))

    if doc.custom_rejoining_approval_status == "Cancelled":
        frappe.throw(_("Rejoining form is already cancelled."))

    for row in APPROVAL_FLOW:
        doc.db_set(row["status_field"], "Cancelled")
    doc.db_set("docstatus", 2)
    doc.db_set("custom_rejoining_approval_status", "Cancelled")

    doc.add_comment("Info", _("Rejoining form cancelled by {0}.").format(
        frappe.bold(frappe.session.user)
    ))

    return True
