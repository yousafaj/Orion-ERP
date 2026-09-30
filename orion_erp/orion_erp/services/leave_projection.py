"""Pure date arithmetic for prospective accrual; never posts leave credits."""

import calendar
from datetime import date


def anniversary(joining, month):
    year, month_index = divmod(joining.year * 12 + joining.month - 1 + month, 12)
    return date(year, month_index + 1, min(joining.day, calendar.monthrange(year, month_index + 1)[1]))


def project_accrual(joining, today, leave_start, rules, period_start, period_end):
    """Only regular credits due after today and by leave start in this allocation.

    Uses the scheduler's first matching service-month rule. Attendance-dependent
    catch-up adjustments are deliberately excluded from this forecast.
    """
    if leave_start <= today:
        return 0.0
    first = max(1, (today.year - joining.year) * 12 + today.month - joining.month)
    last = (leave_start.year - joining.year) * 12 + leave_start.month - joining.month
    total = 0.0
    for month in range(first, last + 1):
        credit_date = anniversary(joining, month)
        if not (today < credit_date <= leave_start and period_start <= credit_date <= period_end):
            continue
        for rule in sorted(rules, key=lambda row: row["from_months"]):
            if rule["from_months"] <= month and (not rule["to_months"] or month <= rule["to_months"]):
                total += float(rule["days_per_month"] or 0)
                break
    return round(total, 2)
