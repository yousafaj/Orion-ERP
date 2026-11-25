"""UAE leave rules enforced on Leave Application / Leave Type (wired in hooks.py)."""
import re
from datetime import date

import frappe
from frappe import _
from frappe.utils import add_days, add_months, cint, flt, getdate, today

from orion_erp.leave_management.tiers import split_by_tier, sum_in_period


# ----------------------------------------------------------------- helpers
def get_leave_year(company, on_date):
    """Active Leave Period containing on_date, else the calendar year."""
    on_date = getdate(on_date)
    lp = frappe.db.get_value(
        "Leave Period",
        {"company": company, "is_active": 1, "from_date": ["<=", on_date], "to_date": [">=", on_date]},
        ["from_date", "to_date"],
    )
    if lp:
        return getdate(lp[0]), getdate(lp[1])
    return date(on_date.year, 1, 1), date(on_date.year, 12, 31)


# def get_pay_tiers(leave_type):
#     """[(up_to_day, pay_fraction)] from the Pay Tiers table on the Leave Type."""
#     lt = frappe.get_cached_doc("Leave Type", leave_type)
#     rows = sorted(lt.get("pay_tiers") or [], key=lambda r: flt(r.up_to_day))
#     return [(flt(r.up_to_day), flt(r.pay_percent) / 100.0) for r in rows]

def get_pay_tiers(leave_type):
    """[(up_to_day, pay_fraction)] from the Leave Pay Tier rows of this Leave Type."""
    rows = frappe.get_all(
        "Leave Pay Tier",
        filters={"parent": leave_type, "parenttype": "Leave Type"},
        fields=["up_to_day", "pay_percent"],
        order_by="up_to_day asc",
    )
    return [(flt(r.up_to_day), flt(r.pay_percent) / 100.0) for r in rows]

def get_holidays(employee, start, end):
    from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

    holiday_list = get_holiday_list_for_employee(employee, raise_exception=False)
    if not holiday_list:
        return set()
    dates = frappe.get_all(
        "Holiday",
        filters={
            "parent": holiday_list,
            "parenttype": "Holiday List",
            "holiday_date": ["between", [start, end]],
        },
        pluck="holiday_date",
    )
    return {getdate(d) for d in dates}


def expand_days(from_date, to_date, half_day, half_day_date, holidays, clip_start, clip_end):
    """One (date, day_fraction) per counted leave day, clipped to the leave year."""
    start, end = max(getdate(from_date), clip_start), min(getdate(to_date), clip_end)
    days, d = [], start
    while d <= end:
        if d not in holidays:
            half = half_day and half_day_date and getdate(half_day_date) == d
            days.append((d, 0.5 if half else 1.0))
        d = add_days(d, 1)
    return days


def build_timeline(employee, leave_type, year_start, year_end, current=None):
    """All approved leave days of this type in the leave year, sorted by date.
    `current` (an unsaved/draft Leave Application) is added in place of its saved copy."""
    include_holiday = cint(frappe.db.get_value("Leave Type", leave_type, "include_holiday"))
    holidays = set() if include_holiday else get_holidays(employee, year_start, year_end)
    apps = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "docstatus": 1,
            "status": "Approved",
            "from_date": ["<=", year_end],
            "to_date": [">=", year_start],
        },
        fields=["name", "from_date", "to_date", "half_day", "half_day_date"],
    )
    if current is not None:
        apps = [a for a in apps if a.name != current.name]
        apps.append(
            frappe._dict(
                name=current.name,
                from_date=current.from_date,
                to_date=current.to_date,
                half_day=current.half_day,
                half_day_date=current.half_day_date,
            )
        )
    days = []
    for a in apps:
        days += expand_days(a.from_date, a.to_date, a.half_day, a.half_day_date, holidays, year_start, year_end)
    return sorted(days, key=lambda x: x[0])


# ------------------------------------------------- Leave Application checks
def validate_leave_application(doc, method=None):
    lt = frappe.get_cached_doc("Leave Type", doc.leave_type)
    emp = frappe.get_cached_doc("Employee", doc.employee)
    _check_gender_religion(lt, emp)
    _check_min_days(doc, lt)
    _check_one_time(doc, lt)
    _check_event(doc, lt)
    _check_document(doc, lt)
    _set_pay_breakdown(doc)


def _check_gender_religion(lt, emp):
    gender = lt.get("gender_restriction")
    if gender in ("Male", "Female") and emp.gender != gender:
        frappe.throw(_("{0} is only available to {1} employees.").format(lt.name, gender))
    religion = lt.get("religion_restriction")
    if religion and (emp.get("religion") or "").strip().lower() != religion.strip().lower():
        frappe.throw(_("{0} is only available to {1} employees.").format(lt.name, religion))


def _check_min_days(doc, lt):
    minimum = flt(lt.get("min_days_per_application"))
    if minimum and flt(doc.total_leave_days) < minimum:
        frappe.throw(_("{0} must be at least {1} days.").format(lt.name, minimum))


def _check_one_time(doc, lt):
    if not lt.get("one_time_only"):
        return
    used = frappe.db.exists(
        "Leave Application",
        {
            "employee": doc.employee,
            "leave_type": doc.leave_type,
            "docstatus": ["<", 2],
            "status": ["in", ["Open", "Approved"]],
            "name": ["!=", doc.name or ""],
        },
    )
    if used:
        frappe.throw(
            _("{0} can be used only once during employment. {1} already exists for this employee.").format(
                lt.name, frappe.utils.get_link_to_form("Leave Application", used)
            )
        )


def _check_event(doc, lt):

    return

    # event_value = doc.get("event_date") or (
    #     doc.get("custom_child_date_of_birth") if lt.name == "Paternity Leave" else None
    # )
    # if not event_value:
    #     frappe.throw(_("Enter the Event Date (birth, death or expected delivery date) for {0}.").format(lt.name))
    # event, first_day = getdate(event_value), getdate(doc.from_date)
    # # if not lt.get("requires_event_date"):
    # #     return
    # # if not doc.get("event_date"):
    # #     frappe.throw(_("Enter the Event Date (birth, death or expected delivery date) for {0}.").format(lt.name))
    # event, first_day = getdate(doc.event_date), getdate(doc.from_date)
    # before = cint(lt.get("event_allow_before_days"))
    # if first_day < add_days(event, -before):
    #     frappe.throw(_("Leave cannot start more than {0} days before the event date.").format(before))
    # months = cint(lt.get("event_window_months"))
    # if months and first_day > getdate(add_months(event, months)):
    #     frappe.throw(_("{0} must start within {1} months of the event date.").format(lt.name, months))


def _check_document(doc, lt):
    # if lt.get("document_mode") == "Mandatory" and not doc.get("supporting_document"):
    if lt.get("document_mode") == "Mandatory" and not (
        doc.get("supporting_document") or doc.get("custom_medical_certificate")
    ):
        frappe.throw(_("A supporting document is required for {0}. Attach it before saving.").format(lt.name))


def _set_pay_breakdown(doc):
    """Fill full / half / unpaid days. Informational: payroll always recalculates from scratch."""
    doc.full_pay_days = doc.half_pay_days = doc.unpaid_days = 0
    tiers = get_pay_tiers(doc.leave_type)
    if not tiers or not doc.from_date or not doc.to_date:
        return
    # year_start, year_end = get_leave_year(doc.company, doc.from_date)
    year_start, year_end = get_tier_window(doc.employee, doc.leave_type, doc.from_date, doc.company, doc.get("event_date"))
    timeline = build_timeline(doc.employee, doc.leave_type, year_start, year_end, current=doc)
    mine = sum_in_period(split_by_tier(timeline, tiers), getdate(doc.from_date), getdate(doc.to_date))
    doc.full_pay_days = mine.get(1.0, 0)
    doc.half_pay_days = mine.get(0.5, 0)
    doc.unpaid_days = mine.get(0.0, 0)


# ------------------------------------------------------------ Leave Type
def block_casual_leave(doc, method=None):
    if re.search(r"casual", f"{doc.name or ''} {doc.leave_type_name or ''}", re.I):
        frappe.throw(
            _("Casual Leave does not exist under UAE Labour Law (Federal Decree-Law No. 33 of 2021) and cannot be created.")
        )


# ------------------------------------------------------------- Scheduler
def send_missing_document_alerts():
    """Daily: email HR about 'Upload later' leaves whose document deadline has passed."""
    from orion_erp.orion_erp.doctype.pre_employment_training.pre_employment_training import get_hr_emails

    lines = []
    for lt in frappe.get_all(
        "Leave Type", filters={"document_mode": "Upload later"}, fields=["name", "document_deadline_days"]
    ):
        apps = frappe.get_all(
            "Leave Application",
            filters={
                "leave_type": lt.name,
                "docstatus": ["<", 2],
                "status": ["in", ["Open", "Approved"]],
                "supporting_document": ["is", "not set"],
            },
            fields=["name", "employee_name", "from_date"],
        )
        for a in apps:
            deadline = add_days(a.from_date, cint(lt.document_deadline_days))
            if getdate(today()) > getdate(deadline):
                lines.append(f"<li>{a.employee_name} - {lt.name} ({a.name}), document was due {deadline}</li>")
    recipients = get_hr_emails()
    if lines and recipients:
        frappe.sendmail(
            recipients=recipients,
            subject=_("Leave documents overdue"),
            message="<p>These leave applications have no supporting document after the deadline:</p><ul>"
            + "".join(lines)
            + "</ul>",
        )


PER_CASE_LEAVE_TYPES = {"Maternity Leave"}   # counted from the first day of the leave, not per leave year


def get_tier_window(employee, leave_type, on_date, company, event_date=None):
    """Sick Leave: the leave year. Maternity: counted from the first day of the case."""
    if leave_type not in PER_CASE_LEAVE_TYPES:
        return get_leave_year(company, on_date)
    on_date = getdate(on_date)
    first = frappe.db.get_value(
        "Leave Application",
        {
            "employee": employee,
            "leave_type": leave_type,
            "docstatus": 1,
            "status": "Approved",
            "from_date": ["<=", on_date],
            "to_date": [">=", add_months(on_date, -12)],
        },
        "from_date",
        order_by="from_date asc",
    )
    start = min(getdate(first), on_date) if first else on_date
    return start, add_days(start, 400)