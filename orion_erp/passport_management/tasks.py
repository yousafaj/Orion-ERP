import frappe
from frappe.utils import today, add_days, formatdate, escape_html

from orion_erp.passport_management.utils import find_expiring_passports


# Days to look back when running the daily expiry reminder, so a missed
# scheduler day doesn't permanently skip a cohort.
EXPIRY_LOOKBACK_DAYS = 2

# Window for deduplicating expiry reminders against the Communication log.
EXPIRY_DEDUP_DAYS = 7


def send_overdue_passport_alerts():
    """Daily: notify HR and PRO about passports not returned past expected date."""
    overdue = frappe.db.sql(
        """
        SELECT name, employee, employee_name, passport_number,
               expected_return_date, department
        FROM `tabPassport Movement`
        WHERE movement_type = 'In'
          AND is_active_record = 1
          AND docstatus = 1
          AND expected_return_date IS NOT NULL
          AND expected_return_date < %(today)s
        ORDER BY expected_return_date ASC
        """,
        {"today": today()},
        as_dict=True,
    )

    if not overdue:
        return

    hr_managers = frappe.get_all(
        "Has Role", filters={"role": "HR Manager", "parenttype": "User"}, fields=["parent"], pluck="parent"
    )
    pros = frappe.get_all(
        "Has Role", filters={"role": "PRO", "parenttype": "User"}, fields=["parent"], pluck="parent"
    )
    recipients = list(set(hr_managers + pros))
    if not recipients:
        return

    rows = "".join(
        "<tr><td>{name}</td><td>{passport}</td>"
        "<td>{dept}</td><td>{expected}</td>"
        "<td><a href='/app/passport-movement/{record_href}'>{record}</a></td></tr>".format(
            name=escape_html(r.employee_name or ""),
            passport=escape_html(r.passport_number or ""),
            dept=escape_html(r.department or ""),
            expected=escape_html(formatdate(r.expected_return_date)),
            record_href=escape_html(r.name),
            record=escape_html(r.name),
        )
        for r in overdue
    )

    message = f"""
    <p>The following passports are overdue for return:</p>
    <table border="1" cellpadding="4" cellspacing="0">
      <thead>
        <tr>
          <th>Employee</th><th>Passport No.</th><th>Department</th>
          <th>Expected Return</th><th>Record</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """

    frappe.sendmail(
        recipients=recipients,
        subject=f"[Passport Management] {len(overdue)} Overdue Passport(s) — {formatdate(today())}",
        message=message,
        delayed=False,
    )


def send_expiry_reminders():
    """Daily: warn employees about passports expiring at 90 / 60 / 30 day thresholds.

    Uses a small lookback window so a missed scheduler day still catches the
    cohort the next time it runs. Deduplicates against the Communication log
    so a given employee isn't reminded twice for the same threshold within a
    week.
    """
    alert_days = [90, 60, 30]
    for days in alert_days:
        target_end = add_days(today(), days)
        target_start = add_days(target_end, -EXPIRY_LOOKBACK_DAYS)

        expiring = list(find_expiring_passports(target_start, target_end))
        if not expiring:
            continue

        subject = f"Passport Expiry Reminder — {days} days remaining"
        dedup_since = add_days(today(), -EXPIRY_DEDUP_DAYS)

        for emp in expiring:
            user_id = frappe.db.get_value("Employee", emp.employee, "user_id")
            if not user_id:
                continue

            already_sent = frappe.db.exists(
                "Communication",
                {
                    "recipients": ["like", f"%{user_id}%"],
                    "subject": subject,
                    "creation": [">=", dedup_since],
                },
            )
            if already_sent:
                continue

            frappe.sendmail(
                recipients=[user_id],
                subject=subject,
                message=(
                    f"<p>Dear {escape_html(emp.employee_name or '')},</p>"
                    f"<p>Your passport <b>{escape_html(emp.passport_number or '')}</b> expires on "
                    f"<b>{escape_html(formatdate(emp.passport_expiry_date))}</b> "
                    f"({days} days from today). Please initiate renewal.</p>"
                ),
                delayed=False,
            )
