import frappe
from frappe import _


def validate_medical_certificate_for_payroll_entry(doc, method=None):
    employees = [row.employee for row in doc.employees if row.employee]
    missing = _get_employees_with_pending_medical_certificates(
        doc.company, doc.start_date, doc.end_date, employees
    )
    if not missing:
        return

    missing_employee_ids = {item.employee for item in missing}

    for item in missing:
        _send_payroll_reminder_to_employee(
            item.employee, item.employee_name, item.leave_application,
            item.leave_type, item.from_date, item.to_date
        )

    hr_emails = _get_hr_user_emails()
    if hr_emails:
        _send_payroll_reminder_to_hr(
            hr_emails, missing, doc.company, doc.start_date, doc.end_date
        )

    skipped_names = []
    rows_to_keep = []
    for row in doc.employees:
        if row.employee in missing_employee_ids:
            skipped_names.append(row.employee_name or row.employee)
        else:
            rows_to_keep.append(row)

    doc.set("employees", [])
    for row in rows_to_keep:
        doc.append("employees", row)

    skipped_list = "".join(f"<li>{name}</li>" for name in skipped_names)
    frappe.msgprint(
        _("The following employees have been <b>skipped</b> from this payroll run "
          "due to pending Medical Certificate submission:<ul>{0}</ul>"
          "Payroll processing will proceed with the remaining employees. "
          "Reminder notifications have been sent to the employees and HR Manager.").format(
            skipped_list
        ),
        title=_("Employees Skipped - Medical Certificate Pending"),
        indicator="orange",
    )


def validate_medical_certificate_for_salary_slip(doc, method=None):
    if doc.docstatus != 0:
        return

    missing = _get_employees_with_pending_medical_certificates(
        doc.company, doc.start_date, doc.end_date, [doc.employee]
    )
    if not missing:
        return

    for item in missing:
        _send_payroll_reminder_to_employee(
            item.employee, item.employee_name, item.leave_application,
            item.leave_type, item.from_date, item.to_date
        )

    hr_emails = _get_hr_user_emails()
    if hr_emails:
        _send_payroll_reminder_to_hr(
            hr_emails, missing, doc.company, doc.start_date, doc.end_date
        )

    items = ", ".join(
        "{0} ({1} to {2})".format(m.leave_application, m.from_date, m.to_date)
        for m in missing
    )

    frappe.throw(
        _("Salary Slip cannot be processed for employee <b>{0}</b>. "
          "The following approved leave application(s) require a Medical Certificate "
          "that has not been uploaded:<br><br>{1}"
          "<br><br>Please upload the required Medical Certificate(s) before proceeding.").format(
            doc.employee_name, items
        ),
        title=_("Medical Certificate Required")
    )


def _get_employees_with_pending_medical_certificates(company, start_date, end_date, employees):
    if not employees:
        return []

    leave_types = frappe.get_all(
        "Leave Type",
        filters={"custom_medical_certificate_required": 1},
        pluck="name"
    )
    if not leave_types:
        return []

    leave_apps = frappe.get_all(
        "Leave Application",
        filters={
            "employee": ["in", employees],
            "company": company,
            "leave_type": ["in", leave_types],
            "docstatus": 1,
            "status": "Approved",
            "from_date": ["<=", end_date],
            "to_date": [">=", start_date],
            "custom_medical_certificate": ["is", "not set"],
        },
        fields=[
            "name",
            "employee",
            "employee_name",
            "leave_type",
            "from_date",
            "to_date",
        ]
    )

    leave_apps_emptystr = frappe.get_all(
        "Leave Application",
        filters={
            "employee": ["in", employees],
            "company": company,
            "leave_type": ["in", leave_types],
            "docstatus": 1,
            "status": "Approved",
            "from_date": ["<=", end_date],
            "to_date": [">=", start_date],
            "custom_medical_certificate": "",
        },
        fields=[
            "name",
            "employee",
            "employee_name",
            "leave_type",
            "from_date",
            "to_date",
        ]
    )

    seen = set()
    result = []
    for item in leave_apps + leave_apps_emptystr:
        if item.name not in seen:
            seen.add(item.name)
            item.leave_application = item.name
            result.append(item)

    return result


def _send_payroll_reminder_to_employee(employee, employee_name, leave_application, leave_type, from_date, to_date):
    user_id = frappe.db.get_value("Employee", employee, "user_id")
    if not user_id:
        return

    leave_link = frappe.utils.get_url() + f"/app/leave-application/{leave_application}"
    subject = _("Reminder: Medical Certificate Required for Payroll Processing")
    message = f"""
    <h3>Medical Certificate Required for Payroll Processing</h3>
    <p>Your leave application <b>{leave_application}</b> for <b>{leave_type}</b> ({from_date} to {to_date}) has been approved but the required Medical Certificate has not yet been uploaded.</p>
    <p><b>Payroll processing has been blocked</b> until the Medical Certificate is uploaded. Please submit the document immediately to avoid delays in your salary.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Application</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{leave_application}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{from_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{to_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Medical Certificate</b></td><td style="padding:8px;border:1px solid #f3f3f3;"><b style="color:red;">Pending</b></td></tr>
    </table>
    <br><a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">Upload Medical Certificate Now</a>
    """
    try:
        frappe.sendmail(recipients=[user_id], subject=subject, message=message, now=True)
    except Exception:
        frappe.log_error(title="Medical Certificate Reminder Email Failed", message=f"Failed to send medical certificate reminder to {user_id}")


def _send_payroll_reminder_to_hr(hr_emails, missing_items, company, start_date, end_date):
    employee_rows = ""
    for item in missing_items:
        leave_link = frappe.utils.get_url() + f"/app/leave-application/{item.leave_application}"
        employee_rows += f"""
        <tr>
            <td style="padding:8px;border:1px solid #f3f3f3;">{item.employee_name}</td>
            <td style="padding:8px;border:1px solid #f3f3f3;">{item.employee}</td>
            <td style="padding:8px;border:1px solid #f3f3f3;">{item.leave_application}</td>
            <td style="padding:8px;border:1px solid #f3f3f3;">{item.leave_type}</td>
            <td style="padding:8px;border:1px solid #f3f3f3;">{item.from_date} to {item.to_date}</td>
            <td style="padding:8px;border:1px solid #f3f3f3;"><a href="{leave_link}">Upload MC</a></td>
        </tr>
        """

    subject = _("Payroll Blocked: Medical Certificate Pending for {0} Employee(s)").format(
        len(missing_items)
    )
    message = f"""
    <h3>Payroll Processing - Medical Certificate Pending</h3>
    <p>The following employees have been <b>skipped</b> from payroll processing for the period <b>{start_date} to {end_date}</b> (Company: <b>{company}</b>) due to pending Medical Certificate submission.</p>
    <p>Please ensure all required Medical Certificates are uploaded to include these employees in the next payroll run.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;">
        <tr style="background-color:#f5f5f5;">
            <th style="padding:8px;border:1px solid #f3f3f3;text-align:left;">Employee Name</th>
            <th style="padding:8px;border:1px solid #f3f3f3;text-align:left;">Employee ID</th>
            <th style="padding:8px;border:1px solid #f3f3f3;text-align:left;">Leave Application</th>
            <th style="padding:8px;border:1px solid #f3f3f3;text-align:left;">Leave Type</th>
            <th style="padding:8px;border:1px solid #f3f3f3;text-align:left;">Leave Period</th>
            <th style="padding:8px;border:1px solid #f3f3f3;text-align:left;">Action</th>
        </tr>
        {employee_rows}
    </table>
    """
    try:
        frappe.sendmail(recipients=hr_emails, subject=subject, message=message, now=True)
    except Exception:
        frappe.log_error(title="Payroll Medical Certificate HR Notification Failed", message=f"Failed to send payroll medical certificate HR notification")


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
        emails = frappe.get_all(
            "User",
            filters={"name": ["in", user_list], "enabled": 1},
            pluck="email"
        )
        users.update(emails)

    return list(users)
