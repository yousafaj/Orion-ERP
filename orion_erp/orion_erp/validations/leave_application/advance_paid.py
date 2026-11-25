import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days
from hrms.hr.doctype.leave_application.leave_application import get_number_of_leave_days
from orion_erp.leave_management import rules
from frappe.utils import get_first_day, get_last_day
from orion_erp.leave_management.payroll import get_daily_rate

COMPONENT = "Leave Already Paid Deduction"
PAY_BASE = 30
REQUIRED_FIELDS = (
    "custom_paid_days_returned", "custom_paid_days_used", "custom_paid_amount",
    "custom_paid_recovered", "custom_paid_recovery_ref",
    "custom_paid_days_covered", "custom_paid_source",
)


def _ready():
    meta = frappe.get_meta("Leave Application")
    return all(meta.has_field(f) for f in REQUIRED_FIELDS)


def _open_sources(employee, leave_type=None):
    filters = {"employee": employee, "docstatus": 1,
               "custom_paid_recovered": 0, "custom_paid_days_returned": [">", 0]}
    if leave_type:
        filters["leave_type"] = leave_type
    rows = frappe.get_all(
        "Leave Application", filters=filters, order_by="creation asc",
        fields=["name", "custom_paid_days_returned", "custom_paid_days_used", "custom_paid_amount"])
    return [r for r in rows if flt(r.custom_paid_days_returned) - flt(r.custom_paid_days_used) > 0]


# ---------------- Recall ----------------
@frappe.whitelist()
def recall_leave(docname, rejoin_date, monthly_salary=None):
    if not _ready():
        frappe.throw(_("Leave Application custom fields are missing."))
    if not set(frappe.get_roles()) & {"HR Manager", "HR User", "System Manager"}:
        frappe.throw(_("Only HR can recall an employee from leave."), frappe.PermissionError)

    doc = frappe.get_doc("Leave Application", docname)
    if doc.docstatus != 1 or doc.status != "Approved":
        frappe.throw(_("Only approved, submitted leave can be recalled."))
    if doc.half_day:
        frappe.throw(_("Half-day leave cannot be recalled."))
    if flt(doc.custom_paid_days_returned) > 0:
        frappe.throw(_("This leave was already recalled."))

    rejoin = getdate(rejoin_date)
    old_to = getdate(doc.to_date)
    if not (getdate(doc.from_date) < rejoin <= old_to):
        frappe.throw(_("Rejoining date must be after the start date and not later than the end date."))

    new_to = add_days(rejoin, -1)
    old_days = flt(doc.total_leave_days)
    new_days = flt(get_number_of_leave_days(
        doc.employee, doc.leave_type, doc.from_date, new_to, None, None, doc.get("holiday_list")))
    returned = flt(old_days - new_days, 2)
    if returned <= 0:
        frappe.throw(_("No leave days to return."))

    # Per-day value = what the Vacation Settlement actually paid
    settlement = frappe.db.get_value(
        "Leave Settlement",
        {"employee": doc.employee, "type_of_settlement": "Vacation Settlement", "docstatus": 1},
        "name", order_by="date_of_settlement desc")
    row = frappe.get_all(
        "Leave Pay",
        filters={"parent": settlement, "parenttype": "Leave Settlement", "leave_type": doc.leave_type},
        fields=["tenure", "amount"], limit=1) if settlement else []
    if row and flt(row[0].tenure) > 0:
        per_day = flt(row[0].amount) / flt(row[0].tenure)
    else:
        salary = flt(monthly_salary)
        if not salary:
            frappe.throw(_("No leave pay found on the Vacation Settlement. Enter the monthly salary."))
        per_day = salary / PAY_BASE
    amount = flt(per_day * returned, 2)

    entries = frappe.get_all(
        "Leave Ledger Entry",
        filters={"transaction_type": "Leave Application", "transaction_name": doc.name, "docstatus": 1},
        pluck="name")
    if len(entries) != 1:
        frappe.throw(_("This leave spans several allocations; recall it manually."))
    frappe.db.set_value("Leave Ledger Entry", entries[0], {"leaves": -new_days, "to_date": new_to})

    # cancel "On Leave" attendance from the rejoining date

        # 1. cancel On Leave attendance from the rejoining date
    for att in frappe.get_all(
        "Attendance",
        filters={"employee": doc.employee, "leave_application": doc.name,
                 "status": "On Leave", "docstatus": 1,
                 "attendance_date": ["between", [rejoin, old_to]]},
        pluck="name"):
        frappe.get_doc("Attendance", att).cancel()

    # 2. shorten the leave BEFORE creating Present rows
    doc.db_set({
        "to_date": new_to, "total_leave_days": new_days,
        "custom_paid_days_returned": returned, "custom_paid_days_used": 0,
        "custom_paid_amount": amount, "custom_paid_recovered": 0,
    })

    # 3. mark Present on working days he actually worked
    holidays = rules.get_holidays(doc.employee, rejoin, old_to)
    day = rejoin
    while day <= old_to:
        if day not in holidays and not frappe.db.exists(
            "Attendance", {"employee": doc.employee, "attendance_date": day, "docstatus": ["<", 2]}):
            att = frappe.get_doc({"doctype": "Attendance", "employee": doc.employee,
                                  "attendance_date": day, "status": "Present", "company": doc.company})
            att.flags.ignore_permissions = True
            att.insert()
            att.submit()
        day = add_days(day, 1)

    doc.add_comment("Info", _("Recalled on {0}. {1} days returned to balance; already paid in leave salary ({2}).")
                    .format(rejoin, returned, amount))
    return {"returned": returned, "amount": amount}


# ---------------- Later leave takes the paid days ----------------
def consume_on_submit(doc, method=None):
    if not _ready() or not doc.employee:
        return
    sources = [s for s in _open_sources(doc.employee, doc.leave_type) if s.name != doc.name]
    if not sources:
        return
    src = sources[0]
    left = flt(src.custom_paid_days_returned) - flt(src.custom_paid_days_used)
    covered = min(flt(doc.total_leave_days), left)
    if covered <= 0:
        return

    start = get_first_day(doc.from_date)
    end = get_last_day(doc.from_date)
    try:
        daily = get_daily_rate(doc.employee, start, end)
    except Exception:
        daily = flt(src.custom_paid_amount) / flt(src.custom_paid_days_returned)
    deduction = flt(daily * covered, 2)

    frappe.db.set_value("Leave Application", src.name,
                        "custom_paid_days_used", flt(src.custom_paid_days_used) + covered)

    add = frappe.new_doc("Additional Salary")
    add.employee = doc.employee
    add.company = doc.company
    add.salary_component = COMPONENT
    add.amount = deduction
    add.payroll_date = getdate(doc.from_date)
    add.overwrite_salary_structure_amount = 1
    add.ref_doctype = "Leave Application"
    add.ref_docname = doc.name
    add.flags.ignore_permissions = True
    add.insert(ignore_permissions=True)
    add.submit()

    doc.db_set({"custom_paid_days_covered": covered, "custom_paid_source": src.name})
    doc.add_comment("Info", _("{0} days were already paid (leave salary). {1} deducted in payroll.")
                    .format(covered, deduction))


def restore_on_cancel(doc, method=None):
    if not _ready():
        return
    for name in frappe.get_all(
        "Additional Salary",
        filters={"ref_doctype": "Leave Application", "ref_docname": doc.name,
                 "salary_component": COMPONENT, "docstatus": 1}, pluck="name"):
        frappe.get_doc("Additional Salary", name).cancel()
    src, covered = doc.get("custom_paid_source"), flt(doc.get("custom_paid_days_covered"))
    if src and covered > 0 and frappe.db.exists("Leave Application", src):
        used = flt(frappe.db.get_value("Leave Application", src, "custom_paid_days_used"))
        frappe.db.set_value("Leave Application", src, "custom_paid_days_used", max(used - covered, 0))
    doc.db_set({"custom_paid_days_covered": 0, "custom_paid_source": None})


# ---------------- Final Settlement ----------------
def remaining_value(employee):
    if not _ready():
        return 0.0
    total = 0.0
    for s in _open_sources(employee):
        left = flt(s.custom_paid_days_returned) - flt(s.custom_paid_days_used)
        total += flt(s.custom_paid_amount) / flt(s.custom_paid_days_returned) * left
    return flt(total, 2)


def apply_leave_advance_recovery(doc):
    if not _ready():
        doc.leave_advance_recovery = 0
        return
    doc.leave_advance_recovery = (
        remaining_value(doc.employee)
        if doc.type_of_settlement == "Final Settlement" and doc.employee else 0)


def mark_recovered(doc):
    if not _ready() or flt(doc.get("leave_advance_recovery")) <= 0:
        return
    for s in _open_sources(doc.employee):
        frappe.db.set_value("Leave Application", s.name,
                            {"custom_paid_recovered": 1, "custom_paid_recovery_ref": doc.name})


def reopen(doc):
    if not _ready():
        return
    for name in frappe.get_all("Leave Application",
                               filters={"custom_paid_recovery_ref": doc.name}, pluck="name"):
        frappe.db.set_value("Leave Application", name,
                            {"custom_paid_recovered": 0, "custom_paid_recovery_ref": None})
            

@frappe.whitelist()
def get_vacation_leave_pay(employee, date_of_settlement, monthly_salary=None):
    salary = flt(monthly_salary)
    if not employee or not salary:
        return []
    settings = frappe.get_single("Orion Settings")
    types = [r.leave_type for r in (settings.get("leave_types_for_accrual") or []) if r.leave_type]
    if not types:
        return []
    apps = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee, "docstatus": 1, "status": "Approved",
            "leave_type": ["in", types],
            "to_date": [">=", getdate(date_of_settlement)],
            "custom_vacation_settlement": ["is", "not set"],
        },
        fields=["name", "leave_type", "from_date", "to_date", "total_leave_days"],
        order_by="from_date asc")
    return [{
        "leave_application": a.name, "leave_type": a.leave_type,
        "from": a.from_date, "to": a.to_date, "tenure": flt(a.total_leave_days),
        "amount": flt(salary / PAY_BASE * flt(a.total_leave_days), 2),
    } for a in apps]


def link_vacation_leave(doc):
    if doc.type_of_settlement != "Vacation Settlement":
        return
    for row in doc.leave_pay or []:
        if row.get("leave_application"):
            frappe.db.set_value("Leave Application", row.leave_application,
                                "custom_vacation_settlement", doc.name)


def unlink_vacation_leave(doc):
    for name in frappe.get_all("Leave Application",
                               filters={"custom_vacation_settlement": doc.name}, pluck="name"):
        frappe.db.set_value("Leave Application", name, "custom_vacation_settlement", None)



@frappe.whitelist()
def recalc_deduction(leave_application):
    """Rebuild the deduction using the payroll daily rate (for leaves submitted before the rate fix)."""
    doc = frappe.get_doc("Leave Application", leave_application)
    covered = flt(doc.custom_paid_days_covered)
    if covered <= 0:
        frappe.throw(_("This leave has no paid days covered."))

    daily = get_daily_rate(doc.employee, get_first_day(doc.from_date), get_last_day(doc.from_date))
    deduction = flt(daily * covered, 2)

    for name in frappe.get_all(
        "Additional Salary",
        filters={"ref_doctype": "Leave Application", "ref_docname": doc.name,
                 "salary_component": COMPONENT, "docstatus": 1}, pluck="name"):
        frappe.get_doc("Additional Salary", name).cancel()

    add = frappe.new_doc("Additional Salary")
    add.employee = doc.employee
    add.company = doc.company
    add.salary_component = COMPONENT
    add.amount = deduction
    add.payroll_date = getdate(doc.from_date)
    add.overwrite_salary_structure_amount = 1
    add.ref_doctype = "Leave Application"
    add.ref_docname = doc.name
    add.flags.ignore_permissions = True
    add.insert(ignore_permissions=True)
    add.submit()
    return {"daily_rate": daily, "deduction": deduction}




def add_paid_leave_deduction(doc, method=None):
    """Salary Slip validate: deduct leave days that were already paid in a Vacation Settlement."""
    if doc.docstatus != 0 or not doc.employee or not doc.start_date or not _ready():
        return
    start, end = getdate(doc.start_date), getdate(doc.end_date)

    # remove our row first so re-saving never duplicates it
    doc.set("deductions", [d for d in doc.deductions if d.salary_component != COMPONENT])

    apps = frappe.get_all(
        "Leave Application",
        filters={"employee": doc.employee, "docstatus": 1, "status": "Approved",
                 "custom_paid_days_covered": [">", 0],
                 "from_date": ["<=", end], "to_date": [">=", start]},
        fields=["from_date", "to_date", "custom_paid_days_covered"])
    days = 0.0
    for a in apps:
        overlap = (min(getdate(a.to_date), end) - max(getdate(a.from_date), start)).days + 1
        days += min(flt(a.custom_paid_days_covered), max(overlap, 0))
    if days <= 0:
        return

    # un-prorated monthly salary, the same base the slip prorates from
    full = sum(flt(r.default_amount or r.amount) for r in doc.earnings
               if not (r.get("statistical_component") or r.get("do_not_include_in_total")))
    working = flt(doc.total_working_days)
    if not full or not working:
        return
    amount = flt(full / working * days, 2)

    doc.append("deductions", {"salary_component": COMPONENT, "amount": amount})
    doc.total_deduction = sum(flt(d.amount) for d in doc.deductions)
    doc.net_pay = flt(doc.gross_pay) - flt(doc.total_deduction)
    doc.rounded_total = round(doc.net_pay)