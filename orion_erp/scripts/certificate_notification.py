import frappe
from frappe.utils import today, date_diff


def certificate_expiry_notification():

    settings = frappe.get_single("Employee Certificate Notification Settings")

    if settings.disable_notification:
        return

    sent_employee_notifications = set()

    for config in settings.employee_certificate_notification_detail:

        notify_days = config.notify_before_days

        role_recipients = get_users_by_role(config.role)

        filters, or_filters = parse_condition(config.condition)

        employees = frappe.get_all(
            "Employee",
            fields=["name", "user_id"],
            filters=filters,
            or_filters=or_filters
        )

        for emp in employees:

            emp_doc = frappe.get_doc("Employee", emp.name)

            for cert in emp_doc.custom_certificates:
                if cert.certification_name != config.certification_name:
                    continue
                expiry_date = cert.get(config.field_notification_based_on)

                if not expiry_date:
                    continue

                days_left = date_diff(expiry_date, today())

                if days_left != notify_days:
                    continue

                # inject employee fields into cert
                for key, value in emp_doc.as_dict().items():
                    if not hasattr(cert, key):
                        setattr(cert, key, value)

                # inject fields from all employee child tables
                for table in emp_doc.meta.get_table_fields():
                    rows = emp_doc.get(table.fieldname)

                    for row in rows:
                        for key, value in row.as_dict().items():
                            if not hasattr(cert, key):
                                setattr(cert, key, value)
                
                context = {
                    "doc": cert,
                    "employee": emp_doc
                }

                subject = frappe.render_template(config.subject, context)
                message = frappe.render_template(config.message, context)

                recipients = list(role_recipients)

                if config.trigger_email_to_employee and emp_doc.user_id:

                    key = (emp_doc.name, cert.certification_name)

                    if key not in sent_employee_notifications:
                        recipients.append(emp_doc.user_id)
                        sent_employee_notifications.add(key)

                frappe.sendmail(
                    recipients=list(set(recipients)),
                    subject=subject,
                    message=message,
                    sender=config.sender_email
                )


def get_users_by_role(role_name):
    """
    Fetch email IDs of enabled users assigned to a specific role.
    """

    users = frappe.get_all(
        "Has Role",
        filters={"role": role_name},
        pluck="parent"
    )

    if not users:
        return []

    emails = frappe.get_all(
        "User",
        filters={
            "name": ["in", users],
            "enabled": 1
        },
        pluck="email"
    )

    return list(set(emails))

import re

def parse_condition(condition):
    """
    Convert condition
    into frappe filters and or_filters
    """

    if not condition:
        return {}, []

    condition = condition.replace("doc.", "")

    filters = {}
    or_filters = []

    # split OR
    or_parts = [p.strip() for p in condition.split(" or ")]

    for part in or_parts:

        and_parts = [p.strip() for p in part.split(" and ")]

        temp = []

        for cond in and_parts:

            match = re.match(r'(\w+)\s*==\s*["\'](.+?)["\']', cond)

            if match:
                field, value = match.groups()

                if len(or_parts) == 1:
                    filters[field] = value
                else:
                    temp.append([field, "=", value])

        if temp:
            or_filters.extend(temp)

    return filters, or_filters