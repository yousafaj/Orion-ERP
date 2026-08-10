import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days

from .approvals import APPROVAL_FLOW, is_leave_override_user
from .sandwich import (
    get_sandwich_additional_days,
    _sandwich_applies_for_employee,
    _get_configured_sandwich_day_names,
    _get_sandwich_adjustments,
    _count_weekdays_in_range,
    _get_sandwich_dates,
)
from .eligibility import get_completed_months


@frappe.whitelist()
def get_override_roles():
    return frappe.get_all(
        "Role Details",
        filters={"parent": "Orion Settings", "parentfield": "leave_override_roles"},
        pluck="role"
    )


@frappe.whitelist()
def get_employee_details(employee):

    data = frappe.get_all(

        "Employee",

        filters={
            "name": employee
        },

        fields=[

            "employee_name",

            "company",

            "department",

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


# =========================================================
# CANCEL DRAFT LEAVE APPLICATION
# =========================================================

@frappe.whitelist()
def cancel_draft_leave(docname):
    doc = frappe.get_doc("Leave Application", docname)

    if doc.docstatus != 0:
        frappe.throw(_("Only draft leave applications can be cancelled."))

    if doc.status == "Cancelled":
        frappe.throw(_("Leave application is already cancelled."))

    if getdate(doc.from_date) <= getdate():
        frappe.throw(_("Leave cannot be cancelled after the start date has passed."))

    doc.db_set("status", "Cancelled")
    doc.db_set("custom_status_approver1", "Cancelled")
    doc.db_set("custom_status_approver2", "Cancelled")
    doc.db_set("custom_status_approver4", "Cancelled")
    doc.db_set("custom_status_approver5", "Cancelled")
    doc.db_set("docstatus", 2)
    doc.db_set("custom_approval_status", "Cancelled")

    # Cancel linked Leave Declaration if not already being cancelled from LD
    if not frappe.flags.get("cancelling_from_leave_declaration"):
        from .approvals import _cancel_linked_leave_declaration
        _cancel_linked_leave_declaration(doc.name)

    doc.add_comment(
        "Info",
        _("Leave application cancelled by {0} before start date.").format(
            frappe.bold(frappe.session.user)
        )
    )

    return True


# =========================================================
# SEND FOR APPROVAL
# =========================================================

@frappe.whitelist()
def send_for_approval(docname):
    doc = frappe.get_doc("Leave Application", docname)

    if doc.docstatus != 0:
        frappe.throw(_("Only draft Leave Applications can be sent for approval."))

    if doc.custom_approval_status != "Open":
        frappe.throw(_("Leave Application has already been sent for approval."))

    if not doc.leave_approver:
        frappe.throw(_("No leave approver is set for this leave application."))

    doc.custom_sent_for_approval = 1
    doc.custom_approval_status = "Pending Approval from Approver 1"
    doc.custom_last_status_change = frappe.utils.now_datetime()
    doc.custom_reminder_sent = 0
    doc.custom_escalation_sent = 0

    frappe.flags.in_send_for_approval = True
    doc.save(ignore_permissions=True)
    frappe.flags.in_send_for_approval = False

    from .notifications import send_first_approval_email
    send_first_approval_email(doc)

    return True


# =========================================================
# LEAVE TYPE FILTER
# < 6 months → Orion Settings allowed types (ignore allocations)
# >= 6 months → only allocated leave types
# =========================================================

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_leave_types_for_employee(doctype, txt, searchfield, start, page_len, filters):
    employee = filters.get("employee") if filters else None
    if not employee:
        return frappe.db.sql("""
            SELECT name FROM `tabLeave Type`
            WHERE name LIKE %(txt)s
            LIMIT %(start)s, %(page_len)s
        """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

    doj = frappe.db.get_value("Employee", employee, "date_of_joining")
    if not doj:
        return frappe.db.sql("""
            SELECT name FROM `tabLeave Type`
            WHERE name LIKE %(txt)s
            LIMIT %(start)s, %(page_len)s
        """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

    completed_months = get_completed_months(getdate(doj), getdate())

    # Employee within 6 months → show only Orion Settings allowed types
    if completed_months < 6:
        allowed_types = frappe.get_all(
            "Leave Type Details",
            filters={"parent": "Orion Settings", "parentfield": "leave_types_within_six_months"},
            pluck="leave_type"
        )

        if not allowed_types:
            return frappe.db.sql("""
                SELECT name FROM `tabLeave Type`
                WHERE name LIKE %(txt)s
                LIMIT %(start)s, %(page_len)s
            """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

        return frappe.db.sql("""
            SELECT name FROM `tabLeave Type`
            WHERE name IN %(allowed_types)s
              AND name LIKE %(txt)s
            LIMIT %(start)s, %(page_len)s
        """, {"allowed_types": allowed_types, "txt": f"%{txt}%", "start": start, "page_len": page_len})

    # Employee 6+ months → show only allocated leave types
    allocated_types = frappe.db.sql("""
        SELECT DISTINCT leave_type
        FROM `tabLeave Allocation`
        WHERE employee = %(employee)s
          AND docstatus = 1
          AND expired = 0
          AND CURDATE() BETWEEN from_date AND to_date
    """, {"employee": employee}, pluck="leave_type")

    if not allocated_types:
        return []

    return frappe.db.sql("""
        SELECT name FROM `tabLeave Type`
        WHERE name IN %(allocated_types)s
          AND name LIKE %(txt)s
        LIMIT %(start)s, %(page_len)s
    """, {"allocated_types": allocated_types, "txt": f"%{txt}%", "start": start, "page_len": page_len})


# ---------------------------------------------------------------------------
# Monkey-patch storage for LeaveApplication methods
# ---------------------------------------------------------------------------
_original_get_number_of_leave_days = None
_original_update_attendance = None
_original_cancel_attendance = None


def _save_original_get_number_of_leave_days(func):
    global _original_get_number_of_leave_days
    _original_get_number_of_leave_days = func


def _save_original_update_attendance(func):
    global _original_update_attendance
    _original_update_attendance = func


def _save_original_cancel_attendance(func):
    global _original_cancel_attendance
    _original_cancel_attendance = func


# ---------------------------------------------------------------------------
# Patched methods
# ---------------------------------------------------------------------------
@frappe.whitelist()
def patched_get_number_of_leave_days(
    employee, leave_type, from_date, to_date,
    half_day=None, half_day_date=None, holiday_list=None,
):
    result = _original_get_number_of_leave_days(employee, leave_type, from_date, to_date, half_day, half_day_date, holiday_list)

    if _sandwich_applies_for_employee(employee):
        configured_day_names = _get_configured_sandwich_day_names(leave_type)
        additional = get_sandwich_additional_days(leave_type, from_date, to_date, employee)
        if configured_day_names:
            configured_holidays, non_configured_working_weekends = _get_sandwich_adjustments(
                employee, from_date, to_date, configured_day_names
            )
            return max(flt(result) + additional + configured_holidays - non_configured_working_weekends, 0)

    weekdays = _count_weekdays_in_range(from_date, to_date)
    return min(flt(result), weekdays)


def patched_update_attendance(self):
    """Create Attendance records for date range AND sandwich days."""
    _original_update_attendance(self)

    sandwich_dates = _get_sandwich_dates(self.leave_type, self.from_date, self.to_date, self.employee)
    for date_str in sandwich_dates:
        attendance_name = frappe.db.exists(
            "Attendance",
            dict(
                employee=self.employee,
                attendance_date=date_str,
                docstatus=("!=", 2),
            ),
        )
        if not attendance_name:
            doc = frappe.new_doc("Attendance")
            doc.employee = self.employee
            doc.employee_name = self.employee_name
            doc.attendance_date = date_str
            doc.company = self.company
            doc.leave_type = self.leave_type
            doc.leave_application = self.name
            doc.status = "On Leave"
            doc.flags.ignore_validate = True
            doc.insert(ignore_permissions=True)
            doc.submit()


@frappe.whitelist()
def create_leave_application_draft(employee, leave_type, company=None, employee_name=None):
    """Save a minimal Leave Application draft to get a real doc name
    before uploading medical certificate or other attachments.

    Bypasses mandatory field validation since the user may not have
    filled in dates/reason yet."""
    doc = frappe.new_doc("Leave Application")
    doc.employee = employee
    doc.leave_type = leave_type
    doc.company = company
    doc.employee_name = employee_name
    doc.status = "Open"
    doc.custom_approval_status = "Open"

    frappe.flags.creating_leave_draft = True
    doc.insert(ignore_permissions=True, ignore_mandatory=True)
    frappe.flags.creating_leave_draft = False

    return doc.name


def patched_cancel_attendance(self):
    """Cancel Attendance records for date range AND sandwich days."""
    _original_cancel_attendance(self)

    sandwich_dates = _get_sandwich_dates(self.leave_type, self.from_date, self.to_date, self.employee)
    for date_str in sandwich_dates:
        attendance_name = frappe.db.exists(
            "Attendance",
            dict(
                employee=self.employee,
                attendance_date=date_str,
                docstatus=1,
                leave_application=self.name,
            ),
        )
        if attendance_name:
            frappe.db.set_value("Attendance", attendance_name, "docstatus", 2)


def update_medical_certificate_status_on_file_attach(doc, method=None):
    if doc.attached_to_doctype != "Leave Application":
        return
    if doc.attached_to_field != "custom_medical_certificate":
        return

    status = frappe.db.get_value("Leave Application", doc.attached_to_name, "custom_medical_certificate_status")
    if status == "Submitted":
        return

    frappe.db.set_value("Leave Application", doc.attached_to_name, "custom_medical_certificate_status", "Submitted")
    frappe.db.set_value("Leave Application", doc.attached_to_name, "custom_medical_certificate", doc.file_url)


def reset_medical_certificate_status_on_file_trash(doc, method=None):
    if doc.attached_to_doctype != "Leave Application":
        return
    if doc.attached_to_field != "custom_medical_certificate":
        return

    frappe.db.set_value("Leave Application", doc.attached_to_name, "custom_medical_certificate_status", "Pending")
    frappe.db.set_value("Leave Application", doc.attached_to_name, "custom_medical_certificate", "")
