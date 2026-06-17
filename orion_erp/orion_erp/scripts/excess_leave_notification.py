import frappe
from frappe.utils import getdate, today, fmt_money, get_url


def notify_excess_leaves(employee, allocation_name, excess_days, max_carry):
    hr_users = get_hr_user_emails()
    if not hr_users:
        return

    emp_name = frappe.db.get_value("Employee", employee, "employee_name")
    url = get_url(f"/app/leave-allocation/{allocation_name}")
    if not url:
        url = f"/app/leave-allocation/{allocation_name}"
    allocation_url = url

    subject = f"Excess Leave Alert - {emp_name} ({employee})"

    message = f"""
    <h3>Excess Leave Notification</h3>
    <p><b>Employee:</b> {emp_name} ({employee})</p>
    <p><b>Excess Leave Days:</b> {excess_days} day(s)</p>
    <p><b>Carry Over Limit:</b> {max_carry} day(s)</p>
    <p>The employee has excess leave days that need your review.</p>
    <p>
        <a href="{allocation_url}"
           style="display: inline-block; padding: 10px 20px;
                  background-color: #2490ef; color: #fff;
                  text-decoration: none; border-radius: 4px;">
            Review Leave Allocation
        </a>
    </p>
    <p>You can either <b>Forfeit</b> or <b>Extend (Carry Forward)</b> the excess days.</p>
    """

    if not hasattr(frappe.local, "assets_json") or frappe.local.assets_json is None:
        frappe.local.assets_json = {}

    try:
        frappe.sendmail(
            recipients=hr_users,
            subject=subject,
            message=message,
            now=True,
        )
    except Exception:
        frappe.log_error(
            title="Excess Leave Notification Failed",
            message=f"Failed to send excess leave notification for {employee} ({allocation_name})",
        )


def get_hr_user_emails():
    roles = ["HR Manager", "HR User"]
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
