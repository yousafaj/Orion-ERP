import frappe
from frappe.utils import (
    flt, getdate, today, add_months, add_days, date_diff,
    get_first_day, get_last_day,
)
from hrms.hr.doctype.leave_application.leave_application import (
    validate_leave_access,
    get_leave_details as _hrms_get_leave_details,
)

PRORATE_BASE = 30
RETRO_FROM_MONTH = 7

# Used only if the Leave Type has no accrual rules table rows.
DEFAULT_RULES = [
    {"from_months": 1, "to_months": 6, "days_per_month": 2.0},
    {"from_months": 7, "to_months": 0, "days_per_month": 2.5},
]


def _get_rules(leave_type):
    doc = frappe.get_cached_doc("Leave Type", leave_type)
    rows = doc.get("custom_annual_leave_accrual_rules") or []
    rules = [
        {
            "from_months": r.from_months,
            "to_months": r.to_months,
            "days_per_month": flt(r.days_per_month),
        }
        for r in sorted(rows, key=lambda x: x.from_months)
    ]
    return rules or DEFAULT_RULES


def _rate_for_index(idx, rules):
    """idx = calendar month number since joining; joining month = 1."""
    for r in rules:
        if r["to_months"] == 0:
            if idx >= r["from_months"]:
                return r["days_per_month"]
        elif r["from_months"] <= idx <= r["to_months"]:
            return r["days_per_month"]
    return 0


def _is_accrual_type(leave_type):
    settings = frappe.get_single("Orion Settings")
    return leave_type in {
        r.leave_type for r in (settings.get("leave_types_for_accrual") or [])
    }


def _year_no(doj, d):
    """Leave year number (1-based). Leave years run anniversary to anniversary."""
    n = 1
    while add_months(doj, 12 * n) <= d:
        n += 1
    return n


def _year_bounds(doj, year_no):
    start = add_months(doj, 12 * (year_no - 1))
    end = add_days(add_months(doj, 12 * year_no), -1)
    return start, end


def _build_rows(doj, upto, rules):
    """
    One row per calendar month (or part of a month when the anniversary
    falls inside it), from the joining date up to `upto`.

    Once the employee has reached month RETRO_FROM_MONTH, every month in the
    schedule is paid at the current rate (2 -> 2.5). Before that, each month
    uses its own rate.
    """
    upto_idx = (upto.year - doj.year) * 12 + (upto.month - doj.month) + 1
    current_rate = _rate_for_index(upto_idx, rules)
    reprice_all = upto_idx >= RETRO_FROM_MONTH

    rows = []
    m = get_first_day(doj)
    while m <= upto:
        m_end = get_last_day(m)
        idx = (m.year - doj.year) * 12 + (m.month - doj.month) + 1
        rate = current_rate if reprice_all else _rate_for_index(idx, rules)

        start = max(m, doj)
        end = min(m_end, upto)

        # split the month where a leave year begins (anniversary)
        cuts = [start]
        n = 1
        while True:
            anniversary = add_months(doj, 12 * n)
            if anniversary > end:
                break
            if start < anniversary <= end:
                cuts.append(anniversary)
            n += 1
        cuts.append(add_days(end, 1))

        for i in range(len(cuts) - 1):
            s, e = cuts[i], add_days(cuts[i + 1], -1)
            days = date_diff(e, s) + 1
            full = s == m and e == m_end
            credit = rate if full else rate / PRORATE_BASE * min(days, PRORATE_BASE)
            rows.append({
                "year": _year_no(doj, s),
                "month": m.strftime("%b %Y"),
                "index": idx,
                "rate": rate,
                "credit": flt(credit, 2),
                "note": "" if full else f"{days} days",
            })
        m = add_months(m, 1)
    return rows


def _year_rows(rows, year_no):
    """Rows of one leave year with a running cumulative total."""
    out, total = [], 0.0
    for r in rows:
        if r["year"] != year_no:
            continue
        total = flt(total + r["credit"], 2)
        out.append({**r, "cumulative": total})
    return out


def _consumed(employee, leave_type, year_start, year_end):
    used = frappe.db.sql(
        """
        SELECT IFNULL(SUM(total_leave_days), 0) FROM `tabLeave Application`
        WHERE employee=%s AND leave_type=%s AND docstatus=1
          AND from_date BETWEEN %s AND %s
        """,
        (employee, leave_type, year_start, year_end),
    )[0][0]

    pending = frappe.db.sql(
        """
        SELECT IFNULL(SUM(total_leave_days), 0) FROM `tabLeave Application`
        WHERE employee=%s AND leave_type=%s AND docstatus=0
          AND from_date BETWEEN %s AND %s
          AND status NOT IN ('Rejected','Cancelled')
          AND IFNULL(custom_approval_status,'') NOT IN ('Rejected','Cancelled')
        """,
        (employee, leave_type, year_start, year_end),
    )[0][0]
    return flt(used), flt(pending)


def _carry_in(employee, leave_type, doj, year_no, rules):
    """
    Unused leave carried into leave year `year_no`.
    Each past year: carry = min(carry_in + accrued - used, max carry).
    Returns (carried, excess_over_limit) for the last year-end before year_no.
    """
    lt = frappe.db.get_value(
        "Leave Type", leave_type,
        ["is_carry_forward", "maximum_carry_forwarded_leaves"], as_dict=True)
    if not lt or not lt.is_carry_forward:
        return 0.0, 0.0
    max_carry = flt(lt.maximum_carry_forwarded_leaves)  # 0 = unlimited

    carry, excess = 0.0, 0.0
    for y in range(1, year_no):
        ys, ye = _year_bounds(doj, y)
        yr = _year_rows(_build_rows(doj, ye, rules), y)
        accrued = yr[-1]["cumulative"] if yr else 0.0
        used, _pending = _consumed(employee, leave_type, ys, ye)
        balance = max(carry + accrued - used, 0)
        if max_carry and balance > max_carry:
            carry, excess = max_carry, balance - max_carry
        else:
            carry, excess = balance, 0.0
    return flt(carry, 2), flt(excess, 2)


@frappe.whitelist()
def get_annual_leave_accrual(employee, leave_type, from_date=None, to_date=None):
    validate_leave_access(employee)

    if not _is_accrual_type(leave_type):
        return {}

    doj = frappe.db.get_value("Employee", employee, "date_of_joining")
    if not doj:
        return {}
    doj = getdate(doj)

    now = getdate(today())
    if doj > now:
        return {}

    leave_start = getdate(from_date) if from_date else now
    target = max(now, leave_start)

    rules = _get_rules(leave_type)
    rows = _build_rows(doj, target, rules)

    # ---- as of today (current leave year) ----
    year_now = _year_no(doj, now)
    rows_now = _build_rows(doj, now, rules)
    sched_now = _year_rows(rows_now, year_now)
    accrued_year_now = sched_now[-1]["cumulative"] if sched_now else 0.0
    carry_now, excess_now = _carry_in(employee, leave_type, doj, year_now, rules)
    accrued_now = flt(accrued_year_now + carry_now, 2)
    ys, ye = _year_bounds(doj, year_now)
    used, pending = _consumed(employee, leave_type, ys, ye)

    # ---- as of leave start (may be a later leave year) ----
    year_start_no = _year_no(doj, target)
    sched_target = _year_rows(rows, year_start_no)
    accrued_year_start = sched_target[-1]["cumulative"] if sched_target else 0.0
    carry_start, excess_start = _carry_in(employee, leave_type, doj, year_start_no, rules)
    accrued_at_start = flt(accrued_year_start + carry_start, 2)
    ys2, ye2 = _year_bounds(doj, year_start_no)
    used2, pending2 = _consumed(employee, leave_type, ys2, ye2)

    return {
        "date_of_joining": str(doj),
        "leave_year": year_start_no,
        "leave_year_from": str(ys2),
        "leave_year_to": str(ye2),
        "schedule": sched_target,
        "carried_forward": carry_now,
        "excess_over_limit": excess_now,
        "accrued_this_year": accrued_year_now,
        "accrued_to_date": accrued_now,
        "used": used,
        "pending": pending,
        "available_now": flt(accrued_now - used - pending, 2),
        "carried_forward_at_start": carry_start,
        "accrued_by_leave_start": accrued_at_start,
        "available_at_leave_start": flt(accrued_at_start - used2 - pending2, 2),
    }


@frappe.whitelist()
def get_accrual_for_employee(employee, from_date=None):
    """Accrual figures for every leave type listed in Orion Settings."""
    validate_leave_access(employee)
    settings = frappe.get_single("Orion Settings")
    types = [r.leave_type for r in (settings.get("leave_types_for_accrual") or []) if r.leave_type]
    out = {}
    for lt in types:
        d = get_annual_leave_accrual(employee, lt, from_date)
        if d:
            out[lt] = d
    return out


@frappe.whitelist()
def get_leave_details(employee, date):
    """Replaces the HRMS call that fills the Allocated Leaves table."""
    result = _hrms_get_leave_details(employee, date)
    for leave_type, row in (result.get("leave_allocation") or {}).items():
        if not _is_accrual_type(leave_type):
            continue
        d = get_annual_leave_accrual(employee, leave_type)
        if not d:
            continue
        row["total_leaves"] = d["accrued_to_date"]
        row["leaves_taken"] = d["used"]
        row["leaves_pending_approval"] = d["pending"]
        row["remaining_leaves"] = d["available_now"]
    return result