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
    doc.db_set("custom_initial_approver_status", "Cancelled")
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
    doc.check_permission("write")
    if frappe.session.user not in (doc.owner, doc.custom_employee_user_id) and not is_leave_override_user():
        frappe.throw(_("Only the initiator or employee can send this leave application for approval."))

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
# Allocated, unpaid and explicitly permitted leave types at leave start
# =========================================================

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_leave_types_for_employee(doctype, txt, searchfield, start, page_len, filters):
    employee = filters.get("employee") if filters else None
    reference_date = getdate((filters or {}).get("from_date"))
    if not employee:
        return []
    from hrms.hr.doctype.leave_application.leave_application import validate_leave_access
    validate_leave_access(employee)
    # Allocation and leave-specific validation decide eligibility. Service length
    # must not hide unrelated allocated leave or unpaid leave from new employees.
    return frappe.db.sql("""
        SELECT lt.name FROM `tabLeave Type` lt
        WHERE lt.name LIKE %(txt)s AND (
            lt.is_lwp = 1
            OR EXISTS (SELECT 1 FROM `tabLeave Allocation` la
                WHERE la.employee = %(employee)s AND la.leave_type = lt.name
                  AND la.docstatus = 1 AND la.expired = 0
                  AND %(date)s BETWEEN la.from_date AND la.to_date)
            OR EXISTS (SELECT 1 FROM `tabLeave Type Details` accrual
                JOIN `tabLeave Allocation` current_la ON current_la.leave_type = accrual.leave_type
                WHERE accrual.parent = 'Orion Settings'
                  AND accrual.parentfield = 'leave_types_for_accrual'
                  AND accrual.leave_type = lt.name AND current_la.employee = %(employee)s
                  AND current_la.docstatus = 1 AND current_la.expired = 0
                  AND %(today)s BETWEEN current_la.from_date AND current_la.to_date
                  AND %(date)s > current_la.to_date
                  AND %(date)s <= DATE_ADD(current_la.to_date, INTERVAL 1 YEAR))
            OR EXISTS (SELECT 1 FROM `tabLeave Type Details` allowed
                WHERE allowed.parent = 'Orion Settings'
                  AND allowed.parentfield = 'leave_types_within_six_months'
                  AND allowed.leave_type = lt.name)
        ) ORDER BY lt.name LIMIT %(start)s, %(page_len)s
    """, {"employee": employee, "date": reference_date, "today": getdate(), "txt": f"%{txt}%",
            "start": start, "page_len": page_len})


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
    if not frappe.has_permission("Leave Application", "create"):
        frappe.throw(_("You do not have permission to create a Leave Application."), frappe.PermissionError)
    doc = frappe.new_doc("Leave Application")
    doc.employee = employee
    from .initiators import validate_leave_initiator
    validate_leave_initiator(doc)
    doc.leave_type = leave_type
    doc.company = company
    doc.employee_name = employee_name
    doc.status = "Open"
    doc.custom_initial_approver_status = "Open"
    doc.custom_approval_status = "Open"

    try:
        frappe.flags.creating_leave_draft = True
        doc.insert(ignore_permissions=True, ignore_mandatory=True)
    finally:
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


# Keep the original public hook paths compatible with existing sites.
from orion_erp.orion_erp.services.medical_certificate import (
    update_medical_certificate_status_on_file_attach,
    reset_medical_certificate_status_on_file_trash,
)
