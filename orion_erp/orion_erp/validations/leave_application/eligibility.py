import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days, add_months


def add_eligibility_warning(doc, title, message):
    separator = "\n" if doc.custom_eligibility_warnings else ""
    doc.custom_eligibility_warnings = (doc.custom_eligibility_warnings or "") + separator + message
    frappe.throw(
        title=_(title),
        msg=_(message)
    )


def validate_annual_leave_avail(doc, method=None):
    if doc.docstatus == 1:
        return

    settings = frappe.get_single("Orion Settings")
    configured_types = [
        row.leave_type
        for row in (getattr(settings, "leave_types_requiring_one_year_service", None) or [])
        if row.leave_type
    ]

    if not configured_types or doc.leave_type not in configured_types:
        return

    employee_doj = frappe.db.get_value("Employee", doc.employee, "date_of_joining")
    if not employee_doj:
        return

    doj = getdate(employee_doj)
    today = getdate()

    if doj > today:
        add_eligibility_warning(
            doc,
            "Leave Eligibility",
            "Employee has not yet joined. Recruitment date is {0}.".format(employee_doj)
        )
        return

    completed_months = get_completed_months(doj, today)

    balance = frappe.db.sql("""
        SELECT COALESCE(SUM(leaves), 0)
        FROM `tabLeave Ledger Entry`
        WHERE employee = %s
          AND leave_type = %s
          AND docstatus = 1
          AND is_expired = 0
    """, (doc.employee, doc.leave_type))[0][0] or 0

    balance = flt(balance)

    if completed_months < 12:
        add_eligibility_warning(
            doc,
            "Leave Eligibility",
            "You must complete 1 year of service to apply for {0} days {1}. "
            "Your current accrued balance is {2} days.".format(
                doc.total_leave_days, doc.leave_type, balance
            )
        )


def get_completed_months(doj, ref_date):
    months = (ref_date.year - doj.year) * 12 + (ref_date.month - doj.month)
    if ref_date.day < doj.day:
        months -= 1
    return max(0, months)


def validate_medical_certificate(doc, method=None):
    if not doc.leave_type:
        return

    leave_type = frappe.db.get_value(
        "Leave Type",
        doc.leave_type,
        [
            "custom_medical_certificate_required",
            "custom_medical_certificate_required_by"
        ],
        as_dict=True
    )

    if not leave_type or not leave_type.custom_medical_certificate_required:
        doc.custom_medical_certificate_status = ""
        return

    if doc.custom_medical_certificate:
        doc.custom_medical_certificate_status = "Submitted"
        return

    # For List View / Reports
    doc.custom_medical_certificate_status = "Pending"

    hrs_text = ""
    if leave_type.custom_medical_certificate_required_by:
        hrs_text = _(
            " The certificate should be submitted within {0} hours."
        ).format(leave_type.custom_medical_certificate_required_by)

    frappe.msgprint(
        title=_("Medical Certificate Required"),
        indicator="orange",
        msg=_(
            "A medical certificate is required for the selected leave type and has not yet been attached."
        ) + hrs_text
    )

def validate_paternity_leave(doc, method=None):
    settings = frappe.get_single("Orion Settings")
    configured_type = getattr(settings, "paternity_leave_type", None)
    eligibility_months = getattr(settings, "paternity_leave_eligibility_months", None) or 6

    if not configured_type or doc.leave_type != configured_type:
        return

    if not doc.custom_child_date_of_birth:
        add_eligibility_warning(
            doc,
            "Paternity Leave Eligibility",
            "Child's Date of Birth is required for {0}.".format(doc.leave_type)
        )
        return

    child_dob = getdate(doc.custom_child_date_of_birth)
    cutoff_date = add_months(child_dob, eligibility_months)

    if doc.from_date and getdate(doc.from_date) > cutoff_date:
        add_eligibility_warning(
            doc,
            "Paternity Leave Eligibility",
            "{0} must be taken within {1} months of the child's date of birth. From Date ({2}) exceeds the {1}-month period from child's date of birth ({3}).".format(
                doc.leave_type,
                eligibility_months,
                str(doc.from_date),
                str(doc.custom_child_date_of_birth)
            )
        )

    if doc.to_date and getdate(doc.to_date) > cutoff_date:
        add_eligibility_warning(
            doc,
            "Paternity Leave Eligibility",
            "{0} must be taken within {1} months of the child's date of birth. To Date ({2}) exceeds the {1}-month period from child's date of birth ({3}).".format(
                doc.leave_type,
                eligibility_months,
                str(doc.to_date),
                str(doc.custom_child_date_of_birth)
            )
        )


def validate_hajj_umrah_leave(doc, method=None):
    settings = frappe.get_single("Orion Settings")
    configured_type = getattr(settings, "hajj_umrah_leave_type", None)

    if not configured_type or doc.leave_type != configured_type:
        return

    eligible_religions_str = getattr(settings, "hajj_umrah_eligible_religions", None) or "Muslim"
    eligible_religions = [r.strip() for r in eligible_religions_str.split(",") if r.strip()]
    allow_once_only = getattr(settings, "hajj_umrah_allow_once_only", 1)

    religion = frappe.db.get_value("Employee", doc.employee, "custom_religion")
    if religion not in eligible_religions:
        add_eligibility_warning(
            doc,
            "Ineligible",
            "{0} is only applicable to {1} employees.".format(
                doc.leave_type,
                "/".join(eligible_religions)
            )
        )
        return

    max_days = frappe.db.get_value("Leave Type", doc.leave_type, "max_leaves_allowed") or 0
    if max_days and doc.total_leave_days > max_days:
        add_eligibility_warning(
            doc,
            "Exceeds Maximum Leave Days",
            "{0} cannot exceed {1} days as per the Leave Type configuration. You have requested {2} days.".format(
                doc.leave_type,
                str(max_days),
                str(doc.total_leave_days)
            )
        )

    if allow_once_only:
        existing = frappe.db.exists("Leave Application", {
            "employee": doc.employee,
            "leave_type": doc.leave_type,
            "docstatus": 1,
            "status": "Approved",
            "name": ["!=", doc.name]
        })

        if existing:
            add_eligibility_warning(
                doc,
                "Already Availed",
                "Employee has already availed {0}. This leave type can only be availed once during the entire employment period.".format(
                    doc.leave_type
                )
            )
