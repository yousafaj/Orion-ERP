"""Turns half-pay / unpaid tier days into itemised Additional Salary deductions.

Flow for HR: Payroll Entry -> Get Employees -> Leave Pay > Preview / Create Leave Deductions
-> Submit -> Create Salary Slips. Salary slips then show e.g.
"Sick Leave Deduction - Half Pay" and "Sick Leave Deduction - Unpaid" as separate lines.
"""
import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, getdate
from orion_erp.leave_management import rules
from orion_erp.leave_management.tiers import split_by_tier, sum_in_period

# ---- settings ----
BASIC_COMPONENT = "Basic"
SALARY_BASIS = "GROSS"       # "GROSS" = all earnings of the salary structure, "BASIC" = BASIC_COMPONENT only
DAILY_RATE_MODE = "CALENDAR"
                             # "WORKING_DAYS" = salary / days that are not holidays
FIXED_DAYS = 30
PAY_LABELS = {0.5: "Half Pay", 0.0: "Unpaid"}

def component_name(leave_type, pay_fraction):
    return f"{leave_type} Deduction - {PAY_LABELS[pay_fraction]}"


def tier_leave_types():
    return sorted(set(frappe.get_all("Leave Pay Tier", filters={"parenttype": "Leave Type"}, pluck="parent")))


def _unprorate(slip, amount):
    pd, wd = flt(slip.payment_days), flt(slip.total_working_days)
    if pd and wd and pd < wd:
        return flt(amount) * wd / pd
    return flt(amount)


def get_monthly_basic(employee, on_date):
    ssa = frappe.db.get_value(
        "Salary Structure Assignment",
        {"employee": employee, "docstatus": 1, "from_date": ["<=", on_date]},
        ["salary_structure", "base"],
        as_dict=True,
        order_by="from_date desc",
    )
    if not ssa:
        frappe.throw(_("No Salary Structure Assignment found for {0}.").format(employee))
    try:
        from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

        slip = make_salary_slip(
            ssa.salary_structure, employee=employee, posting_date=on_date, for_preview=1, ignore_permissions=True
        )
        total = 0.0
        for row in slip.earnings:
            amount = flt(row.default_amount or row.amount)
            if SALARY_BASIS == "BASIC":
                if row.salary_component == BASIC_COMPONENT:
                    return _unprorate(slip, amount)
            elif not (row.get("statistical_component") or row.get("do_not_include_in_total")):
                total += amount
        if SALARY_BASIS == "GROSS" and total:
            return _unprorate(slip, total)
    except Exception:
        frappe.log_error(title="Leave deduction: could not preview salary slip", message=frappe.get_traceback())
    return flt(ssa.base)  # fallback


def get_daily_rate(employee, start, end):
    salary = get_monthly_basic(employee, end)
    if DAILY_RATE_MODE == "WORKING_DAYS":
        days = max(date_diff(end, start) + 1 - len(rules.get_holidays(employee, start, end)), 1)
    elif DAILY_RATE_MODE == "CALENDAR":
        days = date_diff(end, start) + 1  # days in the payroll period: 31 for January, 28 for February
    else:
        days = FIXED_DAYS
    return flt(salary / days, 6)


# ------------------------------------------------------------ calculation
def calculate(pe):
    start, end = getdate(pe.start_date), getdate(pe.end_date)
    employees = [r.employee for r in (pe.get("employees") or [])]
    if not employees:
        frappe.throw(_("Click 'Get Employees' on the Payroll Entry first, then save."))

    rows = []
    for leave_type in tier_leave_types():
        tiers = rules.get_pay_tiers(leave_type)
        if not tiers:
            continue
        apps = frappe.get_all(
            "Leave Application",
            filters={
                "employee": ["in", employees],
                "leave_type": leave_type,
                "docstatus": 1,
                "status": "Approved",
                "from_date": ["<=", end],
                "to_date": [">=", start],
            },
            fields=["employee", "from_date"],
        )
        seen = set()
        for a in apps:
            emp = a.employee
            per_case = leave_type in rules.PER_CASE_LEAVE_TYPES
            on_date = getdate(a.from_date) if per_case else max(getdate(a.from_date), start)
            w_start, w_end = rules.get_tier_window(emp, leave_type, on_date, pe.company)
            if (emp, w_start) in seen:
                continue
            seen.add((emp, w_start))
            timeline = rules.build_timeline(emp, leave_type, w_start, w_end)
            totals = sum_in_period(split_by_tier(timeline, tiers), start, end)
            deductible = {p: d for p, d in totals.items() if p < 1.0 and d}
            if not deductible:
                continue
            daily = get_daily_rate(emp, start, end)
            name = frappe.db.get_value("Employee", emp, "employee_name")
            for pay, days in deductible.items():
                if pay not in PAY_LABELS:
                    frappe.throw(_("{0}: only 50% and 0% pay tiers are supported.").format(leave_type))
                rows.append(
                    {
                        "employee": emp,
                        "employee_name": name,
                        "leave_type": leave_type,
                        "pay_percent": pay * 100,
                        "days": days,
                        "daily_rate": daily,
                        "amount": flt(days * (1 - pay) * daily, 2),
                        "component": component_name(leave_type, pay),
                    }
                )
    return rows

# -------------------------------------------------------------- endpoints
@frappe.whitelist()
def preview_leave_deductions(payroll_entry):
    pe = frappe.get_doc("Payroll Entry", payroll_entry)
    pe.check_permission("read")
    return calculate(pe)


@frappe.whitelist()
def create_leave_deductions(payroll_entry):
    pe = frappe.get_doc("Payroll Entry", payroll_entry)
    pe.check_permission("write")
    end, start = getdate(pe.end_date), getdate(pe.start_date)
    rows = calculate(pe)
    wanted = {(r["employee"], r["component"]) for r in rows}
    created, unchanged, blocked = 0, 0, []

    def slip_exists(emp):
        return frappe.db.exists(
            "Salary Slip", {"employee": emp, "start_date": start, "end_date": end, "docstatus": ["<", 2]}
        )

    # cancel deductions made earlier by this Payroll Entry that no longer apply
    for old in frappe.get_all(
        "Additional Salary",
        filters={"ref_doctype": "Payroll Entry", "ref_docname": pe.name, "docstatus": 1},
        fields=["name", "employee", "salary_component"],
    ):
        if (old.employee, old.salary_component) not in wanted and not slip_exists(old.employee):
            frappe.get_doc("Additional Salary", old.name).cancel()

    for r in rows:
        existing = frappe.db.get_value(
            "Additional Salary",
            {
                "employee": r["employee"],
                "salary_component": r["component"],
                "payroll_date": end,
                "ref_docname": pe.name,
                "docstatus": 1,
            },
            ["name", "amount"],
            as_dict=True,
        )
        if existing:
            if abs(flt(existing.amount) - r["amount"]) < 0.01:
                unchanged += 1
                continue
            if slip_exists(r["employee"]):
                blocked.append(f"{r['employee_name']}: salary slip already exists, cancel it first")
                continue
            frappe.get_doc("Additional Salary", existing.name).cancel()
        doc = frappe.get_doc(
            {
                "doctype": "Additional Salary",
                "employee": r["employee"],
                "company": pe.company,
                "salary_component": r["component"],
                "amount": r["amount"],
                "payroll_date": end,
                "overwrite_salary_structure_amount": 1,
                "ref_doctype": "Payroll Entry",
                "ref_docname": pe.name,
            }
        )
        doc.insert()
        doc.submit()
        created += 1

    return {"created": created, "unchanged": unchanged, "blocked": blocked}


ABSENT_LIKE = ("Absent", "On Leave")


def _holiday_absence_dates(employee, start, end):
    """Unmarked holidays sitting between two absent / on-leave stretches
    (at least one side a real absence)."""
    holidays = rules.get_holidays(employee, start, end)
    if not holidays:
        return []
    marked = {
        getdate(r.attendance_date): r.status
        for r in frappe.get_all(
            "Attendance",
            filters={"employee": employee, "docstatus": ["<", 2], "attendance_date": ["between", [start, end]]},
            fields=["attendance_date", "status"],
        )
    }
    joined, left = frappe.db.get_value("Employee", employee, ["date_of_joining", "relieving_date"])

    def status(d):
        return marked.get(d) or "Absent"  # unmarked working day counts as Absent

    out = []
    for d in sorted(holidays):
        if d in marked:
            continue
        if (joined and d < getdate(joined)) or (left and d > getdate(left)):
            continue
        prev, nxt = add_days(d, -1), add_days(d, 1)
        while prev >= start and prev in holidays:
            prev = add_days(prev, -1)
        while nxt <= end and nxt in holidays:
            nxt = add_days(nxt, 1)
        if prev < start or nxt > end:
            continue
        before, after = status(prev), status(nxt)
        if before in ABSENT_LIKE and after in ABSENT_LIKE and "Absent" in (before, after):
            out.append(d)
    return out


def auto_mark_holiday_absences(doc, method=None):
    """Salary Slip before_validate: holidays between absent/leave stretches become Absent attendance,
    so the slip's absent and payment days count them."""
    if doc.docstatus != 0 or not doc.employee or not doc.start_date or not doc.end_date:
        return
    if frappe.db.get_single_value("Payroll Settings", "payroll_based_on") != "Attendance":
        return
    for d in _holiday_absence_dates(doc.employee, getdate(doc.start_date), getdate(doc.end_date)):
        att = frappe.get_doc(
            {
                "doctype": "Attendance",
                "employee": doc.employee,
                "attendance_date": d,
                "status": "Absent",
                "company": doc.company,
            }
        )
        att.flags.ignore_permissions = True
        att.insert()
        att.submit()