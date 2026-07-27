import frappe
from frappe import _


def _is_medical_certificate_pending(doc):
    if not doc.leave_type:
        return False
    required = frappe.db.get_value("Leave Type", doc.leave_type, "custom_medical_certificate_required")
    if not required:
        return False
    return not doc.custom_medical_certificate


def _notify_medical_certificate_pending(doc):
    leave_link = frappe.utils.get_url() + f"/app/leave-application/{doc.name}"

    employee_email = doc.get("custom_employee_user_id")
    if employee_email:
        emp_subject = _("Medical Certificate Required - {0}").format(doc.name)
        emp_message = f"""
        <h3>Medical Certificate Required</h3>
        <p>Your leave application <b>{doc.name}</b> has been approved. However, a Medical Certificate is required for <b>{doc.leave_type}</b> and has not yet been uploaded.</p>
        <p>Please upload the Medical Certificate at the earliest to avoid any payroll impact.</p>
        <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
            <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
            <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.from_date}</td></tr>
            <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.to_date}</td></tr>
            <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Medical Certificate</b></td><td style="padding:8px;border:1px solid #f3f3f3;"><b style="color:red;">Pending</b></td></tr>
        </table>
        <br><a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">Upload Medical Certificate</a>
        """
        try:
            frappe.sendmail(recipients=[employee_email], subject=emp_subject, message=emp_message, now=True)
        except Exception:
            frappe.log_error(title="Medical Certificate Reminder Email Failed", message=f"Failed to send medical certificate reminder to {employee_email}")

    hr_emails = _get_hr_user_emails()
    if hr_emails:
        hr_subject = _("Approved Leave Missing Medical Certificate - {0}").format(doc.name)
        hr_message = f"""
        <h3>Approved Leave Missing Medical Certificate</h3>
        <p>The following leave application has been approved but is missing the mandatory Medical Certificate for <b>{doc.leave_type}</b>.</p>
        <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
            <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Employee</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td></tr>
            <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
            <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.from_date}</td></tr>
            <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.to_date}</td></tr>
            <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Medical Certificate</b></td><td style="padding:8px;border:1px solid #f3f3f3;"><b style="color:red;">Pending</b></td></tr>
        </table>
        <br><a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Leave Application</a>
        """
        try:
            frappe.sendmail(recipients=hr_emails, subject=hr_subject, message=hr_message, now=True)
        except Exception:
            frappe.log_error(title="Medical Certificate HR Notification Failed", message=f"Failed to send medical certificate HR notification for {doc.name}")


def _get_hr_user_emails():
    try:
        configured_roles = frappe.get_all(
            "Role Details",
            filters={"parent": "Orion Settings", "parentfield": "excess_leave_notification_roles"},
            pluck="role"
        )
        if configured_roles:
            roles = configured_roles
        else:
            roles = ["HR Manager", "HR User"]
    except Exception:
        roles = ["HR Manager", "HR User"]

    if not roles:
        return []

    users = set()
    for role in roles:
        user_list = frappe.get_all(
            "Has Role",
            filters={"role": role, "parenttype": "User"},
            pluck="parent"
        )
        if user_list:
            emails = frappe.get_all(
                "User",
                filters={"name": ["in", user_list], "enabled": 1},
                pluck="email"
            )
            users.update(emails)

    return list(users)


def _notify_rejected(doc, old_doc):
    if not old_doc:
        return
    from .approvals import APPROVAL_FLOW
    was_rejected = any(old_doc.get(row["status_field"]) == "Rejected" for row in APPROVAL_FLOW if doc.get(row["approver_field"]))
    if was_rejected:
        return
    employee_email = doc.get("custom_employee_user_id")
    if not employee_email:
        return
    leave_link = frappe.utils.get_url() + f"/app/leave-application/{doc.name}"
    subject = _("Leave Application Rejected - {0}").format(doc.name)
    message = f"""
    <h3>Leave Application Rejected</h3>
    <p>Your leave application <b>{doc.name}</b> has been rejected.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.from_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.to_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Rejected</td></tr>
    </table>
    <br><a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Application</a>
    """
    try:
        frappe.sendmail(recipients=[employee_email], subject=subject, message=message, now=False)
    except Exception:
        frappe.log_error(title="Leave Rejected Email Failed", message=f"Failed to send rejected leave email to {employee_email}")


def _notify_cancelled(doc, old_doc):
    if not old_doc:
        return
    from .approvals import APPROVAL_FLOW
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

    leave_link = frappe.utils.get_url() + f"/app/leave-application/{doc.name}"
    subject = _("Leave Application Cancelled - {0}").format(doc.name)
    message = f"""
    <h3>Leave Application Cancelled</h3>
    <p>Leave application <b>{doc.name}</b> has been cancelled.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.from_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.to_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Cancelled</td></tr>
    </table>
    <br><a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Application</a>
    """
    try:
        frappe.sendmail(recipients=list(recipients), subject=subject, message=message, now=False)
    except Exception:
        frappe.log_error(title="Leave Cancelled Email Failed", message=f"Failed to send cancelled leave notification for {doc.name}")


def _notify_override_status_change(doc, old_doc):
    if not old_doc:
        return

    from .approvals import APPROVAL_FLOW

    current_user = frappe.session.user
    override_user_name = frappe.db.get_value("User", current_user, "full_name") or current_user

    changed_fields = []
    for row in APPROVAL_FLOW:
        old_val = old_doc.get(row["status_field"])
        new_val = doc.get(row["status_field"])
        if old_val != new_val:
            changed_fields.append((row["status_field"], old_val, new_val))

    if not changed_fields:
        return

    recipients = set()
    employee_email = doc.get("custom_employee_user_id")
    if employee_email:
        recipients.add(employee_email)

    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        if approver:
            recipients.add(approver)

    recipients = {r for r in recipients if frappe.utils.validate_email_address(r, throw=False)}

    if not recipients:
        return

    leave_link = frappe.utils.get_url() + f"/app/leave-application/{doc.name}"

    changes_html = ""
    for field_name, old_val, new_val in changed_fields:
        label = field_name.replace("custom_status_approver", "Approver ").replace("status", "Approver 1")
        changes_html += f"""
            <tr>
                <td style="padding:8px;border:1px solid #f3f3f3;">{label}</td>
                <td style="padding:8px;border:1px solid #f3f3f3;">{old_val or "Open"}</td>
                <td style="padding:8px;border:1px solid #f3f3f3;"><b>{new_val}</b></td>
            </tr>
        """

    subject = _("Leave Application Override Approval - {0}").format(doc.name)
    message = f"""
    <h3>Leave Application - Override Approval</h3>
    <p><b>{override_user_name}</b> has overridden the approval status for leave application <b>{doc.name}</b>.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Employee</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.from_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.to_date}</td></tr>
    </table>
    <br>
    <b>Changes Made:</b>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Level</b></td>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Previous</b></td>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Updated</b></td>
        </tr>
        {changes_html}
    </table>
    <br><a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Application</a>
    """
    try:
        frappe.sendmail(recipients=list(recipients), subject=subject, message=message, now=True)
    except Exception:
        frappe.log_error(title="Override Status Change Email Failed", message=f"Failed to send override status change notification for {doc.name}")


def send_next_approval_email(doc):
    from .approvals import APPROVAL_FLOW

    old_doc = doc.get_doc_before_save()

    if not old_doc:
        return

    last_changed_index = None

    for index, row in enumerate(APPROVAL_FLOW):

        status_field = row["status_field"]

        old_status = old_doc.get(status_field)

        new_status = doc.get(status_field)

        if (
            old_status != "Approved"
            and new_status == "Approved"
        ):
            last_changed_index = index

    if last_changed_index is None:
        return

    next_index = last_changed_index + 1

    next_approver = None
    while next_index < len(APPROVAL_FLOW):
        next_row = APPROVAL_FLOW[next_index]
        next_approver = doc.get(next_row["approver_field"])
        if next_approver:
            break
        next_index += 1

    if not next_approver:
        return

    subject = "Leave Approval Notification"

    leave_link = (
        frappe.utils.get_url()
        + f"/app/leave-application/{doc.name}"
    )

    message = f"""
    <h1>Leave Application Notification</h1>

    <h3>Details:</h3>

    <table class="table table-bordered small"
        style="
            width:100%;
            border-collapse:collapse;
            border:1px solid #f3f3f3;
            max-width:500px
        ">

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                Employee
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                {doc.employee_name}
            </td>
        </tr>

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                Leave Type
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                {doc.leave_type}
            </td>
        </tr>

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                From Date
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                {doc.from_date}
            </td>
        </tr>

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                To Date
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                {doc.to_date}
            </td>
        </tr>

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                Status
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                Pending Approval
            </td>
        </tr>

    </table>

    <br><br>

    <a
        href="{leave_link}"
        target="_blank"
        style="
            color:#fff;
            text-decoration:none;
            padding:4px 20px;
            font-size:13px;
            border-radius:6px;
            background-color:#171717;
            display:inline-block;
            line-height:20px;
        "
    >
        Open Now
    </a>
    """

    try:
        frappe.sendmail(
            recipients=[next_approver],
            subject=subject,
            message=message,
            now=False,
        )
    except Exception:
        frappe.log_error(title="Leave Approval Email Failed", message=f"Failed to send approval email for leave to {next_approver}")


def send_first_approval_email(doc):
    from .approvals import APPROVAL_FLOW

    first_approver = None
    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        if approver:
            first_approver = approver
            break

    if not first_approver:
        return

    subject = "Leave Approval Notification"
    leave_link = frappe.utils.get_url() + f"/app/leave-application/{doc.name}"

    message = f"""
    <h1>Leave Application Notification</h1>
    <h3>A new leave application requires your approval.</h3>

    <table class="table table-bordered small"
        style="
            width:100%;
            border-collapse:collapse;
            border:1px solid #f3f3f3;
            max-width:500px
        ">

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                Employee
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                {doc.employee_name}
            </td>
        </tr>

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                Leave Type
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                {doc.leave_type}
            </td>
        </tr>

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                From Date
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                {doc.from_date}
            </td>
        </tr>

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                To Date
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                {doc.to_date}
            </td>
        </tr>

        <tr>
            <td style="padding:8px; border:1px solid #f3f3f3;">
                Status
            </td>

            <td style="padding:8px; border:1px solid #f3f3f3;">
                Pending Approval
            </td>
        </tr>

    </table>

    <br><br>

    <a
        href="{leave_link}"
        target="_blank"
        style="
            color:#fff;
            text-decoration:none;
            padding:4px 20px;
            font-size:13px;
            border-radius:6px;
            background-color:#171717;
            display:inline-block;
            line-height:20px;
        "
    >
        Open Now
    </a>
    """

    try:
        frappe.sendmail(
            recipients=[first_approver],
            subject=subject,
            message=message,
            now=False,
        )
    except Exception:
        frappe.log_error(title="Leave Submission Email Failed", message=f"Failed to send submission email to {first_approver}")
