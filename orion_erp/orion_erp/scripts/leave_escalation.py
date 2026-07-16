import frappe
from frappe import _
from frappe.utils import flt, now_datetime

APPROVAL_FLOW = [
    {"approver_field": "leave_approver", "status_field": "status"},
    {"approver_field": "custom_leave_approver_1", "status_field": "custom_status_approver1"},
    {"approver_field": "custom_leave_approver_2", "status_field": "custom_status_approver2"},
    {"approver_field": "custom_leave_approver_4", "status_field": "custom_status_approver4"},
    {"approver_field": "custom_leave_approver_5", "status_field": "custom_status_approver5"},
]


def process_leave_escalations():
    settings = frappe.get_single("Orion Settings")
    escalation_roles = _get_escalation_roles(settings)
    if not escalation_roles:
        return

    escalation_users = _get_users_for_roles(escalation_roles)
    if not escalation_users:
        return

    escalation_rules = _build_escalation_rules_map(settings)

    leave_apps = frappe.get_all(
        "Leave Application",
        filters={
            "docstatus": 0,
            "custom_approval_status": ["not in", ["Approved", "Rejected", "Cancelled", "Submit Pending"]],
        },
        fields=[
            "name",
            "employee_name",
            "leave_type",
            "leave_approver",
            "custom_leave_approver_1",
            "custom_leave_approver_2",
            "custom_leave_approver_4",
            "custom_leave_approver_5",
            "status",
            "custom_status_approver1",
            "custom_status_approver2",
            "custom_status_approver4",
            "custom_status_approver5",
            "custom_last_status_change",
            "custom_reminder_sent",
            "custom_escalation_sent",
            "custom_approval_status",
            "creation",
        ],
    )

    for la in leave_apps:
        _process_single_leave(la, escalation_rules, escalation_users)


def _get_escalation_roles(settings):
    roles = []
    for row in settings.get("default_escalation_roles") or []:
        if row.get("role"):
            roles.append(row.get("role"))
    return roles


def _get_users_for_roles(roles):
    if not roles:
        return []
    users = frappe.get_all(
        "Has Role",
        filters={
            "role": ["in", roles],
            "parenttype": "User",
        },
        fields=["parent"],
        pluck="parent",
    )
    return list(set(users))


def _build_escalation_rules_map(settings):
    rules = {}
    for row in settings.get("leave_escalation_rules") or []:
        if row.get("enabled") and row.get("leave_type"):
            rules[row.get("leave_type")] = {
                "reminder_hours": flt(row.get("reminder_hours")) or 48,
                "escalation_hours": flt(row.get("escalation_hours")) or 72,
            }
    return rules


def _process_single_leave(la, escalation_rules, escalation_users):
    if not escalation_users:
        return

    leave_type = la.leave_type
    if not leave_type or leave_type not in escalation_rules:
        return

    rule = escalation_rules[leave_type]

    pending_level = _get_pending_level(la)
    if pending_level is None:
        return

    approver_field = pending_level["approver_field"]
    approver = la.get(approver_field)
    if not approver:
        return

    hours_waiting = _get_hours_waiting(la)
    if hours_waiting is None:
        return

    reminder_hours = rule["reminder_hours"]
    escalation_hours = rule["escalation_hours"]

    if hours_waiting >= escalation_hours and not la.get("custom_escalation_sent"):
        _escalate(la.name, approver_field, approver, escalation_users, leave_type)
    elif hours_waiting >= reminder_hours and not la.custom_reminder_sent:
        _send_reminder(la.name, approver, approver_field, leave_type)


def _get_pending_level(la):
    for row in APPROVAL_FLOW:
        approver_field = row["approver_field"]
        status_field = row["status_field"]
        approver = la.get(approver_field)
        status = la.get(status_field)
        if approver and status == "Open":
            return row
    return None


def _get_hours_waiting(la):
    status_change = la.custom_last_status_change
    if not status_change:
        status_change = la.creation
    if not status_change:
        return None
    delta = now_datetime() - status_change
    return delta.total_seconds() / 3600


def _send_reminder(leave_name, approver, approver_field, leave_type):
    leave_link = frappe.utils.get_url() + f"/app/leave-application/{leave_name}"
    subject = _("Reminder: Leave Approval Pending - {0}").format(leave_name)
    message = f"""
    <h3>Leave Approval Reminder</h3>
    <p>This is a reminder that the following leave application is awaiting your approval as <b>{approver_field}</b>:</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Application</b></td>
            <td style="padding:8px;border:1px solid #f3f3f3;">{leave_name}</td>
        </tr>
        <tr>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td>
            <td style="padding:8px;border:1px solid #f3f3f3;">{leave_type}</td>
        </tr>
        <tr>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td>
            <td style="padding:8px;border:1px solid #f3f3f3;">Pending</td>
        </tr>
    </table>
    <br>
    <a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">
        Review Now
    </a>
    <br><br>
    <p><i>If no action is taken, this application will be auto-escalated to the configured escalation roles.</i></p>
    """

    try:
        frappe.sendmail(recipients=[approver], subject=subject, message=message, now=False)
    except Exception:
        frappe.log_error(title="Leave Reminder Email Failed", message=f"Failed to send leave reminder email to {approver}")
    frappe.db.set_value("Leave Application", leave_name, "custom_reminder_sent", 1)


def _escalate(leave_name, approver_field, current_approver, escalation_users, leave_type):
    leave_link = frappe.utils.get_url() + f"/app/leave-application/{leave_name}"

    users_str = ", ".join(escalation_users)
    leave_app = frappe.get_doc("Leave Application", leave_name)
    leave_app.add_comment(
        "Info",
        _("Escalation notification sent to {0} - no action by {1} within configured time").format(
            users_str, current_approver
        )
    )

    subject = _("Leave Application Escalated - {0}").format(leave_name)
    message = f"""
    <h3>Leave Application Escalated</h3>
    <p>The following leave application has been escalated to you because <b>{current_approver}</b> did not take action within the configured time.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Application</b></td>
            <td style="padding:8px;border:1px solid #f3f3f3;">{leave_name}</td>
        </tr>
        <tr>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td>
            <td style="padding:8px;border:1px solid #f3f3f3;">{leave_type}</td>
        </tr>
        <tr>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Current Approver</b></td>
            <td style="padding:8px;border:1px solid #f3f3f3;">{current_approver}</td>
        </tr>
        <tr>
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td>
            <td style="padding:8px;border:1px solid #f3f3f3;">Pending</td>
        </tr>
    </table>
    <br>
    <a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">
        Review Now
    </a>
    """

    try:
        frappe.sendmail(recipients=escalation_users, subject=subject, message=message, now=False)
    except Exception:
        frappe.log_error(title="Leave Escalation Email Failed", message=f"Failed to send leave escalation email for {leave_name}")
    frappe.db.set_value("Leave Application", leave_name, "custom_escalation_sent", 1)
