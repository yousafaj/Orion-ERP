import frappe
from frappe import _


def validate_medical_certificate_for_payroll_entry(doc, method=None):
    missing = _get_employees_with_pending_medical_certificates(
        doc.company, doc.start_date, doc.end_date,
        [row.employee for row in doc.employees if row.employee]
    )
    if not missing:
        return

    messages = []
    for item in missing:
        messages.append(
            _("- {0}: Leave Application <b>{1}</b> ({2} to {3})").format(
                item.employee_name, item.leave_application,
                item.from_date, item.to_date
            )
        )
        _send_payroll_reminder_to_employee(
            item.employee, item.employee_name, item.leave_application,
            item.leave_type, item.from_date, item.to_date
        )

    frappe.throw(
        _("Payroll cannot be processed. The following employees have approved leave applications "
          "requiring a Medical Certificate that has not been uploaded:<br><br>{0}"
          "<br><br>Please ensure all required Medical Certificates are uploaded before proceeding.").format(
            "<br>".join(messages)
        ),
        title=_("Medical Certificate Required")
    )


def validate_medical_certificate_for_salary_slip(doc, method=None):
    if doc.docstatus != 0:
        return

    missing = _get_employees_with_pending_medical_certificates(
        doc.company, doc.start_date, doc.end_date, [doc.employee]
    )
    if not missing:
        return

    items = ", ".join(
        "{0} ({1} to {2})".format(m.leave_application, m.from_date, m.to_date)
        for m in missing
    )

    for item in missing:
        _send_payroll_reminder_to_employee(
            item.employee, item.employee_name, item.leave_application,
            item.leave_type, item.from_date, item.to_date
        )

    frappe.throw(
        _("Salary Slip cannot be processed. The following approved leave application(s) for employee <b>{0}</b> "
          "require a Medical Certificate that has not been uploaded:<br><br>{1}"
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

    # Also catch cases where custom_medical_certificate is empty string
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
    frappe.sendmail(recipients=[user_id], subject=subject, message=message, now=False)
