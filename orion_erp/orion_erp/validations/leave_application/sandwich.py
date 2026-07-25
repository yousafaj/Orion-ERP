import frappe
from frappe.utils import getdate, add_days


def _sandwich_applies_for_employee(employee):
    """Check if employee's category is in the configured sandwich leave categories.

    Returns True if no categories are configured (apply to all), or if the employee's
    category matches one of the selected categories.
    """
    if not employee:
        return True
    orion_settings = frappe.get_single("Orion Settings")
    categories = [d.employee_category for d in (orion_settings.get("sandwich_leave_categories") or []) if d.employee_category]
    if not categories:
        return True
    emp_cat = frappe.db.get_value("Employee", employee, "custom_employee_category")
    return emp_cat in categories


def _count_weekdays_in_range(from_date, to_date):
    """Count weekdays (Mon-Fri) between from_date and to_date inclusive."""
    frm = getdate(from_date)
    to = getdate(to_date)
    count = 0
    current = frm
    while current <= to:
        if current.weekday() < 5:
            count += 1
        current = add_days(current, 1)
    return count


def _count_weekends_in_range(from_date, to_date):
    """Count weekend days (Sat+Sun) between from_date and to_date inclusive."""
    frm = getdate(from_date)
    to = getdate(to_date)
    total_days = (to - frm).days + 1
    return total_days - _count_weekdays_in_range(from_date, to_date)


def _get_configured_sandwich_day_names(leave_type):
    """Return list of configured sandwich weekday names (e.g. ['Saturday']) for the leave type."""
    lt = frappe.get_cached_doc("Leave Type", leave_type) if frappe.db.exists("Leave Type", leave_type) else None
    if not lt or not lt.get("custom_enable_sandwich_rule"):
        return []
    return [d.weekday for d in (lt.get("custom_sandwich_days") or []) if d.weekday]


def _count_non_configured_weekends_in_range(from_date, to_date, configured_day_names):
    """Count Sat/Sun in range that are NOT in configured_day_names."""
    frm = getdate(from_date)
    to = getdate(to_date)
    count = 0
    current = frm
    while current <= to:
        if current.weekday() == 5 and "Saturday" not in configured_day_names:
            count += 1
        elif current.weekday() == 6 and "Sunday" not in configured_day_names:
            count += 1
        current = add_days(current, 1)
    return count


def _get_sandwich_adjustments(employee, from_date, to_date, configured_day_names):
    """Compute sandwich adjustments for configured categories.

    Returns (configured_holidays, non_configured_working_weekends):
      - configured_holidays: configured sandwich days in range that ARE holidays
        (excluded by HRMS, need to force-add back)
      - non_configured_working_weekends: non-configured weekends in range that are
        NOT holidays (counted by HRMS, need to subtract)
    """
    try:
        from hrms.hr.utils import get_holidays_for_employee
        holidays_list = get_holidays_for_employee(employee, from_date, to_date)
        holiday_dates = set(getdate(h.holiday_date) for h in holidays_list)
    except Exception:
        holiday_dates = set()

    configured_holidays = 0
    non_configured_working_weekends = 0
    frm = getdate(from_date)
    to = getdate(to_date)
    current = frm
    while current <= to:
        if current.weekday() in (5, 6):
            day_name = "Saturday" if current.weekday() == 5 else "Sunday"
            if day_name in configured_day_names:
                if current in holiday_dates:
                    configured_holidays += 1
            else:
                if current not in holiday_dates:
                    non_configured_working_weekends += 1
        current = add_days(current, 1)
    return configured_holidays, non_configured_working_weekends


def get_sandwich_additional_days(leave_type, from_date, to_date, employee=None):
    """Calculate additional sandwich days for the given leave type and date range."""
    if not leave_type or not from_date or not to_date:
        return 0

    orion_settings = frappe.get_single("Orion Settings")
    if not orion_settings.get("enable_sandwich_leave"):
        return 0

    if not _sandwich_applies_for_employee(employee):
        return 0

    lt = frappe.get_cached_doc("Leave Type", leave_type) if frappe.db.exists("Leave Type", leave_type) else None
    if not lt or not lt.get("custom_enable_sandwich_rule"):
        return 0

    configured_days = [d.weekday for d in (lt.get("custom_sandwich_days") or []) if d.weekday]
    if not configured_days:
        return 0

    frm = getdate(from_date)
    to = getdate(to_date)
    range_days = (to - frm).days
    additional = 0

    if "Saturday" in configured_days and (4 - frm.weekday()) % 7 == range_days:
        additional += 1
    if "Sunday" in configured_days and frm.weekday() == 0:
        additional += 1

    return additional


def _get_sandwich_dates(leave_type, from_date, to_date, employee=None):
    """Return list of date strings for sandwich days, or empty list.

    Replicates the sandwich logic from get_sandwich_additional_days
    but returns actual date strings instead of a count.
    """
    if not leave_type or not from_date or not to_date:
        return []

    orion_settings = frappe.get_single("Orion Settings")
    if not orion_settings.get("enable_sandwich_leave"):
        return []

    if not _sandwich_applies_for_employee(employee):
        return []

    lt = frappe.get_cached_doc("Leave Type", leave_type) if frappe.db.exists("Leave Type", leave_type) else None
    if not lt or not lt.get("custom_enable_sandwich_rule"):
        return []

    configured = [d.weekday for d in (lt.get("custom_sandwich_days") or []) if d.weekday]
    if not configured:
        return []

    frm = getdate(from_date)
    to = getdate(to_date)
    range_days = (to - frm).days

    result = []
    if "Saturday" in configured and (4 - frm.weekday()) % 7 == range_days:
        result.append(add_days(frm, (5 - frm.weekday()) % 7).strftime("%Y-%m-%d"))
    if "Sunday" in configured and frm.weekday() == 0:
        result.append(add_days(frm, -1).strftime("%Y-%m-%d"))

    return result
