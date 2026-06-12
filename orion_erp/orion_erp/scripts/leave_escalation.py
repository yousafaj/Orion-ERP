import frappe
from frappe import _
from frappe.utils import now_datetime

APPROVAL_FLOW = [
    {"approver_field": "leave_approver", "status_field": "status"},
    {"approver_field": "custom_leave_approver_1", "status_field": "custom_status_approver1"},
    {"approver_field": "custom_leave_approver_2", "status_field": "custom_status_approver2"},
    {"approver_field": "custom_leave_approver_4", "status_field": "custom_status_approver4"},
    {"approver_field": "custom_leave_approver_5", "status_field": "custom_status_approver5"},
]


def process_leave_escalations():
    settings = frappe.get_single("Orion Settings")
    default_escalation_user = settings.get("default_escalation_user")
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
            "custom_approval_status",
            "creation",
        ],
    )

    for la in leave_apps:
        _process_single_leave(la, escalation_rules, default_escalation_user)


def _build_escalation_rules_map(settings):
    rules = {}
    for row in settings.get("leave_escalation_rules") or []:
        if row.get("enabled") and row.get("leave_type"):
            rules[row["leave_type"]] = {
                "reminder_hours": flt(row.get("reminder_hours")) or 48,
                "escalation_hours": flt(row.get("escalation_hours")) or 72,
            }
    return rules


def _process_single_leave(la, escalation_rules, default_escalation_user):
    if not default_escalation_user:
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

    if hours_waiting >= escalation_hours:
        _escalate(la.name, approver_field, approver, default_escalation_user, leave_type)
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
    <p><i>If no action is taken, this application will be auto-escalated to HR Manager.</i></p>
    """

    frappe.sendmail(recipients=[approver], subject=subject, message=message, now=False)
    frappe.db.set_value("Leave Application", leave_name, "custom_reminder_sent", 1)


def _escalate(leave_name, approver_field, current_approver, escalation_user, leave_type):
    leave_link = frappe.utils.get_url() + f"/app/leave-application/{leave_name}"

    frappe.db.set_value("Leave Application", leave_name, approver_field, escalation_user)
    frappe.db.set_value("Leave Application", leave_name, "custom_last_status_change", now_datetime())
    frappe.db.set_value("Leave Application", leave_name, "custom_reminder_sent", 0)

    leave_app = frappe.get_doc("Leave Application", leave_name)
    leave_app.add_comment(
        "Info",
        _("Auto-escalated from {0} to HR Manager {1} (no action within configured time)").format(
            current_approver, escalation_user
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
            <td style="padding:8px;border:1px solid #f3f3f3;"><b>Previous Approver</b></td>
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

    frappe.sendmail(recipients=[escalation_user], subject=subject, message=message, now=False)

    previous_approver_subject = _("Leave Application Escalated - {0}").format(leave_name)
    previous_approver_message = f"""
    <h3>Leave Application Escalated</h3>
    <p>Leave application <b>{leave_name}</b> has been escalated from you to HR Manager <b>{escalation_user}</b> due to no action within the configured time.</p>
    """

    frappe.sendmail(recipients=[current_approver], subject=previous_approver_subject, message=previous_approver_message, now=False)


def flt(value):
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0
