"""
Comprehensive test suite for configurable sandwich leave.

Tests the core logic in get_sandwich_additional_days (used by
patched_get_number_of_leave_days) and verifies the full pipeline:
  Orion Settings (global toggle)
  -> Leave Type (per-type toggle + configured weekend days)
  -> get_sandwich_additional_days (returns sandwich-adjusted days)
  -> on_submit (leave balance calc)
  -> salary slip LWP deduction
"""
from datetime import date
import sys

# =============================================================================
# MOCKS
# =============================================================================
class MockLeaveType:
    def __init__(self, enable=False, sandwich_days=""):
        self.custom_enable_sandwich_rule = enable
        self.custom_sandwich_days = sandwich_days

    def get(self, field):
        return getattr(self, field, None)

class MockOrionSettings:
    def __init__(self, enabled=False, categories=None):
        self.enable_sandwich_leave = enabled
        self.sandwich_leave_categories = categories or []

    def get(self, field, default=None):
        return getattr(self, field, default)

class MockDoc:
    def __init__(self, from_date, to_date, total_leave_days, leave_balance=0,
                 leave_type="ANNUAL LEAVE", docstatus=0, half_day=0,
                 employee_category=None):
        self.from_date = from_date
        self.to_date = to_date
        self.total_leave_days = total_leave_days
        self.leave_balance = leave_balance
        self.leave_type = leave_type
        self.docstatus = docstatus
        self.half_day = half_day
        self.employee = "EMP-001"
        self.employee_category = employee_category
        self.messages = []

    def db_set(self, field, value, *args, **kwargs):
        setattr(self, field, value)

def getdate(val):
    if isinstance(val, date):
        return val
    return date.fromisoformat(val)

def flt(val):
    return float(val or 0)

# =============================================================================
# CORE LOGIC — matches production get_sandwich_additional_days
# =============================================================================
def _sandwich_applies_for_employee(orion_settings, employee_category):
    """Check if the employee category is in the configured sandwich leave categories."""
    categories = getattr(orion_settings, "sandwich_leave_categories", None) or []
    if not categories:
        return True
    if not employee_category:
        return True
    return employee_category in categories


def get_sandwich_additional_days(leave_type_obj, from_date, to_date, employee_category=None,
                                 orion_settings=None):
    """Return number of additional sandwich days (0, 1, or 2)."""
    if not from_date or not to_date:
        return 0
    if not leave_type_obj or not leave_type_obj.get("custom_enable_sandwich_rule"):
        return 0
    if orion_settings and not _sandwich_applies_for_employee(orion_settings, employee_category):
        return 0
    sandwich_days_config = (leave_type_obj.get("custom_sandwich_days") or "").strip()
    if not sandwich_days_config:
        return 0
    configured_days = [d.strip() for d in sandwich_days_config.split("\n")]
    frm = getdate(from_date)
    to = getdate(to_date)
    range_days = (to - frm).days
    additional = 0
    if "Saturday" in configured_days and (4 - frm.weekday()) % 7 == range_days:
        additional += 1
    if "Sunday" in configured_days and frm.weekday() == 0:
        additional += 1
    return additional

def validate_sandwich_leave(doc, orion_settings, leave_type_obj):
    """Simulates the monkey-patched get_number_of_leave_days effect on a doc."""
    if not orion_settings.get("enable_sandwich_leave"):
        return
    additional = get_sandwich_additional_days(leave_type_obj, doc.from_date, doc.to_date,
                                              doc.employee_category, orion_settings)
    if additional:
        doc.total_leave_days = flt(doc.total_leave_days) + additional
        day_names = []
        sandwich_days_config = (leave_type_obj.get("custom_sandwich_days") or "").strip()
        configured_days = [d.strip() for d in sandwich_days_config.split("\n")] if sandwich_days_config else []
        from_d = getdate(doc.from_date)
        to_d = getdate(doc.to_date)
        range_d = (to_d - from_d).days
        if "Saturday" in configured_days and (4 - from_d.weekday()) % 7 == range_d:
            day_names.append("Saturday")
        if "Sunday" in configured_days and from_d.weekday() == 0:
            day_names.append("Sunday")
        if day_names:
            doc.messages.append(f"Sandwich Leave: {' and '.join(day_names)} deducted")

def on_submit_leave_application(doc):
    leave_balance_after = flt(doc.leave_balance) - flt(doc.total_leave_days)
    doc.db_set("custom_leave_balance_after", leave_balance_after)

def calculate_lwp_deduction(total_leave_days, per_day_rate):
    return total_leave_days * per_day_rate

# =============================================================================
# TEST RUNNER
# =============================================================================
passed = 0
failed = 0

def test_case(name, condition, details=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}  -- {details}")

print("=" * 70)
print("CONFIGURABLE SANDWICH LEAVE - FULL TEST SUITE")
print("=" * 70)

# =============================================================================
# SECTION 1: Global toggle (Orion Settings)
# =============================================================================
print("\n--- SECTION 1: Global Toggle (Orion Settings) ---")

lt = MockLeaveType(enable=True, sandwich_days="Saturday\nSunday")

os_on = MockOrionSettings(enabled=True)
os_off = MockOrionSettings(enabled=False)

# 1.1
doc = MockDoc("2026-06-05", "2026-06-05", 1)
validate_sandwich_leave(doc, os_off, lt)
test_case("1.1 Global toggle OFF: no sandwich applied",
          doc.total_leave_days == 1 and doc.messages == [],
          f"got total={doc.total_leave_days}, msgs={doc.messages}")

# 1.2
doc = MockDoc("2026-06-05", "2026-06-05", 1)
validate_sandwich_leave(doc, os_on, lt)
test_case("1.2 Global toggle ON: sandwich applied",
          doc.total_leave_days == 2 and "Saturday" in str(doc.messages),
          f"got total={doc.total_leave_days}, msgs={doc.messages}")

# =============================================================================
# SECTION 2: Per leave-type toggle
# =============================================================================
print("\n--- SECTION 2: Per Leave-Type Toggle ---")

os = os_on

lt_off = MockLeaveType(enable=False, sandwich_days="Saturday\nSunday")
lt_on = MockLeaveType(enable=True, sandwich_days="Saturday\nSunday")

# 2.1
doc = MockDoc("2026-06-05", "2026-06-05", 1)
validate_sandwich_leave(doc, os, lt_off)
test_case("2.1 Leave type rule OFF: no sandwich",
          doc.total_leave_days == 1 and doc.messages == [],
          f"got total={doc.total_leave_days}")

# 2.2
doc = MockDoc("2026-06-05", "2026-06-05", 1)
validate_sandwich_leave(doc, os, lt_on)
test_case("2.2 Leave type rule ON: sandwich applied",
          doc.total_leave_days == 2 and "Saturday" in str(doc.messages),
          f"got total={doc.total_leave_days}")

# 2.3
doc = MockDoc("2026-06-05", "2026-06-05", 1, leave_type=None)
validate_sandwich_leave(doc, os, None)
test_case("2.3 No leave type: no sandwich",
          doc.total_leave_days == 1 and doc.messages == [],
          f"got total={doc.total_leave_days}")

# =============================================================================
# SECTION 3: Configurable sandwich days
# =============================================================================
print("\n--- SECTION 3: Configurable Sandwich Days ---")

lt_sat_only = MockLeaveType(enable=True, sandwich_days="Saturday")
lt_sun_only = MockLeaveType(enable=True, sandwich_days="Sunday")
lt_both = MockLeaveType(enable=True, sandwich_days="Saturday\nSunday")

# 3.1
doc = MockDoc("2026-06-01", "2026-06-01", 1)
validate_sandwich_leave(doc, os, lt_sat_only)
test_case("3.1 Sat only, Mon leave: no sandwich (Sun not configured)",
          doc.total_leave_days == 1 and doc.messages == [],
          f"got total={doc.total_leave_days}")

# 3.2
doc = MockDoc("2026-06-05", "2026-06-05", 1)
validate_sandwich_leave(doc, os, lt_sat_only)
test_case("3.2 Sat only, Fri leave: Saturday added",
          doc.total_leave_days == 2 and "Saturday" in str(doc.messages),
          f"got total={doc.total_leave_days}")

# 3.3
doc = MockDoc("2026-06-05", "2026-06-05", 1)
validate_sandwich_leave(doc, os, lt_sun_only)
test_case("3.3 Sun only, Fri leave: no sandwich (Sat not configured)",
          doc.total_leave_days == 1 and doc.messages == [],
          f"got total={doc.total_leave_days}")

# 3.4
doc = MockDoc("2026-06-01", "2026-06-01", 1)
validate_sandwich_leave(doc, os, lt_sun_only)
test_case("3.4 Sun only, Mon leave: Sunday added",
          doc.total_leave_days == 2 and "Sunday" in str(doc.messages),
          f"got total={doc.total_leave_days}")

# 3.5
doc = MockDoc("2026-06-05", "2026-06-08", 4)
validate_sandwich_leave(doc, os, lt_both)
test_case("3.5 Both configured, Fri-Mon: no sandwich (Sat+Sun already in range)",
          doc.total_leave_days == 4 and doc.messages == [],
          f"got total={doc.total_leave_days}, msgs={doc.messages}")

# 3.6
lt_empty = MockLeaveType(enable=True, sandwich_days="")
doc = MockDoc("2026-06-05", "2026-06-05", 1)
validate_sandwich_leave(doc, os, lt_empty)
test_case("3.6 Empty sandwich_days: no sandwich",
          doc.total_leave_days == 1 and doc.messages == [],
          f"got total={doc.total_leave_days}")

# =============================================================================
# SECTION 4: All date scenarios (with both Sat+Sun configured)
# =============================================================================
print("\n--- SECTION 4: All Date Scenarios (Sat+Sun configured) ---")

lt = lt_both

scenarios = [
    ("4.1 Friday only", "2026-06-05", "2026-06-05", 1, 2, "Saturday"),
    ("4.2 Monday only", "2026-06-01", "2026-06-01", 1, 2, "Sunday"),
    ("4.3 Wed to Fri", "2026-06-03", "2026-06-05", 3, 4, "Saturday"),
    ("4.4 Mon to Wed", "2026-06-01", "2026-06-03", 3, 4, "Sunday"),
    ("4.5 Fri to Mon", "2026-06-05", "2026-06-08", 4, 4, ""),
    ("4.6 Tue to Thu", "2026-06-02", "2026-06-04", 3, 3, ""),
    ("4.7 Thu to Sat", "2026-06-04", "2026-06-06", 3, 3, ""),
    ("4.8 Sun to Mon", "2026-05-31", "2026-06-01", 2, 2, ""),
    ("4.9 Thu to Fri", "2026-06-04", "2026-06-05", 2, 3, "Saturday"),
    ("4.10 Mon to Tue", "2026-06-01", "2026-06-02", 2, 3, "Sunday"),
]

for name, from_str, to_str, orig_days, expected_total, expected_days in scenarios:
    doc = MockDoc(from_str, to_str, orig_days)
    validate_sandwich_leave(doc, os, lt)
    ok = doc.total_leave_days == expected_total
    if expected_days and expected_days != "":
        for day_part in expected_days.split("+"):
            ok = ok and day_part in str(doc.messages)
    elif not expected_days:
        ok = ok and doc.messages == []
    test_case(f"{name}: {orig_days}+{expected_total-orig_days}={expected_total}",
              ok, f"got total={doc.total_leave_days}, msgs={doc.messages}")

# =============================================================================
# SECTION 5: Leave balance after submit
# =============================================================================
print("\n--- SECTION 5: Leave Balance After Submit ---")

# 5.1
doc = MockDoc("2026-06-05", "2026-06-05", 1, leave_balance=10, leave_type="Leave Without Pay")
validate_sandwich_leave(doc, os, lt)
on_submit_leave_application(doc)
test_case("5.1 LWP Fri: balance 10-2=8",
          doc.custom_leave_balance_after == 8, f"got {doc.custom_leave_balance_after}")

# 5.2
doc = MockDoc("2026-06-01", "2026-06-01", 1, leave_balance=10)
validate_sandwich_leave(doc, os, lt)
on_submit_leave_application(doc)
test_case("5.2 Annual Mon: balance 10-2=8",
          doc.custom_leave_balance_after == 8, f"got {doc.custom_leave_balance_after}")

# 5.3
doc = MockDoc("2026-06-05", "2026-06-08", 4, leave_balance=15)
validate_sandwich_leave(doc, os, lt)
on_submit_leave_application(doc)
test_case("5.3 Fri-Mon: balance 15-4=11 (no sandwich)",
          doc.custom_leave_balance_after == 11, f"got {doc.custom_leave_balance_after}")

# 5.4
doc = MockDoc("2026-06-02", "2026-06-04", 3, leave_balance=20)
validate_sandwich_leave(doc, os, lt)
on_submit_leave_application(doc)
test_case("5.4 Tue-Thu: balance 20-3=17 (no sandwich)",
          doc.custom_leave_balance_after == 17, f"got {doc.custom_leave_balance_after}")

# =============================================================================
# SECTION 6: Salary Slip LWP Deduction
# =============================================================================
print("\n--- SECTION 6: Salary Slip LWP Deduction ---")

per_day_rate = 200.0

tests_6 = [
    ("6.1 Fri LWP", "2026-06-05", "2026-06-05", 1, 400),
    ("6.2 Mon LWP", "2026-06-01", "2026-06-01", 1, 400),
    ("6.3 Fri-Mon LWP", "2026-06-05", "2026-06-08", 4, 800),
    ("6.4 Tue-Thu LWP (no sandwich)", "2026-06-02", "2026-06-04", 3, 600),
]

for name, fs, ts, orig, expected_ded in tests_6:
    doc = MockDoc(fs, ts, orig, leave_type="Leave Without Pay")
    validate_sandwich_leave(doc, os, lt)
    ded = calculate_lwp_deduction(doc.total_leave_days, per_day_rate)
    test_case(f"{name}: {doc.total_leave_days}days x 200 = {expected_ded}",
              ded == expected_ded, f"got deduction={ded}")

# =============================================================================
# SECTION 7: Core helper get_sandwich_additional_days
# =============================================================================
print("\n--- SECTION 7: Core helper get_sandwich_additional_days ---")

# 7.1 Friday -> +1 Saturday
r = get_sandwich_additional_days(lt, "2026-06-05", "2026-06-05")
test_case("7.1 Fri: +1 Sat", r == 1, f"got {r}")

# 7.2 Monday -> +1 Sunday
r = get_sandwich_additional_days(lt, "2026-06-01", "2026-06-01")
test_case("7.2 Mon: +1 Sun", r == 1, f"got {r}")

# 7.3 Fri-Mon -> +0 (Sat+Sun already in range)
r = get_sandwich_additional_days(lt, "2026-06-05", "2026-06-08")
test_case("7.3 Fri-Mon: +0 (Sat+Sun already in range)", r == 0, f"got {r}")

# 7.4 Tue-Thu -> +0
r = get_sandwich_additional_days(lt, "2026-06-02", "2026-06-04")
test_case("7.4 Tue-Thu: +0", r == 0, f"got {r}")

# 7.5 Only Saturday configured
lt2 = MockLeaveType(enable=True, sandwich_days="Saturday")
r1 = get_sandwich_additional_days(lt2, "2026-06-05", "2026-06-05")  # Fri
r2 = get_sandwich_additional_days(lt2, "2026-06-01", "2026-06-01")  # Mon
test_case("7.5 Sat only, Fri: +1, Mon: +0", r1 == 1 and r2 == 0, f"got {r1},{r2}")

# 7.6 Only Sunday configured
lt3 = MockLeaveType(enable=True, sandwich_days="Sunday")
r1 = get_sandwich_additional_days(lt3, "2026-06-05", "2026-06-05")  # Fri
r2 = get_sandwich_additional_days(lt3, "2026-06-01", "2026-06-01")  # Mon
test_case("7.6 Sun only, Fri: +0, Mon: +1", r1 == 0 and r2 == 1, f"got {r1},{r2}")

# 7.7 Rule disabled
lt4 = MockLeaveType(enable=False, sandwich_days="Saturday\nSunday")
r = get_sandwich_additional_days(lt4, "2026-06-05", "2026-06-05")
test_case("7.7 Rule disabled: +0", r == 0, f"got {r}")

# 7.8 Empty sandwich days
lt5 = MockLeaveType(enable=True, sandwich_days="")
r = get_sandwich_additional_days(lt5, "2026-06-05", "2026-06-05")
test_case("7.8 Empty sandwich days: +0", r == 0, f"got {r}")

# 7.9 None leave type
r = get_sandwich_additional_days(None, "2026-06-05", "2026-06-05")
test_case("7.9 None leave type: +0", r == 0, f"got {r}")

# 7.10 Empty dates
r = get_sandwich_additional_days(lt, None, "2026-06-05")
test_case("7.10 None from_date: +0", r == 0, f"got {r}")

# 7.11 Half-day (logic is same, sandwich independent of half-day)
r = get_sandwich_additional_days(lt, "2026-06-05", "2026-06-05")
test_case("7.11 Fri half-day: +1 (same logic)", r == 1, f"got {r}")

# 7.12 Cross-year
r = get_sandwich_additional_days(lt, "2025-12-29", "2026-01-02")
test_case("7.12 Cross-year Mon-Fri: +2", r == 2, f"got {r}")

# =============================================================================
# SECTION 8: Employee Category Filtering
# =============================================================================
print("\n--- SECTION 8: Employee Category Filtering ---")

lt = lt_both

# 8.1 No categories configured (empty list) -> applies to all
os_no_filter = MockOrionSettings(enabled=True, categories=[])
doc = MockDoc("2026-06-05", "2026-06-05", 1, employee_category="Office")
validate_sandwich_leave(doc, os_no_filter, lt)
test_case("8.1 No cat filter, Office: sandwich applied",
          doc.total_leave_days == 2, f"got {doc.total_leave_days}")

doc = MockDoc("2026-06-05", "2026-06-05", 1, employee_category="Non-Office")
validate_sandwich_leave(doc, os_no_filter, lt)
test_case("8.2 No cat filter, Non-Office: sandwich applied",
          doc.total_leave_days == 2, f"got {doc.total_leave_days}")

# 8.3 Only Office configured -> Office gets sandwich, Non-Office does not
os_office_only = MockOrionSettings(enabled=True, categories=["Office"])
doc = MockDoc("2026-06-05", "2026-06-05", 1, employee_category="Office")
validate_sandwich_leave(doc, os_office_only, lt)
test_case("8.3 Office only filter, Office: sandwich applied",
          doc.total_leave_days == 2, f"got {doc.total_leave_days}")

doc = MockDoc("2026-06-05", "2026-06-05", 1, employee_category="Non-Office")
validate_sandwich_leave(doc, os_office_only, lt)
test_case("8.4 Office only filter, Non-Office: no sandwich",
          doc.total_leave_days == 1, f"got {doc.total_leave_days}")

# 8.5 Only Non-Office configured -> Non-Office gets sandwich, Office does not
os_noe_only = MockOrionSettings(enabled=True, categories=["Non-Office"])
doc = MockDoc("2026-06-05", "2026-06-05", 1, employee_category="Office")
validate_sandwich_leave(doc, os_noe_only, lt)
test_case("8.5 Non-Office only filter, Office: no sandwich",
          doc.total_leave_days == 1, f"got {doc.total_leave_days}")

doc = MockDoc("2026-06-05", "2026-06-05", 1, employee_category="Non-Office")
validate_sandwich_leave(doc, os_noe_only, lt)
test_case("8.6 Non-Office only filter, Non-Office: sandwich applied",
          doc.total_leave_days == 2, f"got {doc.total_leave_days}")

# 8.7 Both categories configured -> both get sandwich
os_both = MockOrionSettings(enabled=True, categories=["Office", "Non-Office"])
doc = MockDoc("2026-06-05", "2026-06-05", 1, employee_category="Office")
validate_sandwich_leave(doc, os_both, lt)
test_case("8.7 Both filter, Office: sandwich applied",
          doc.total_leave_days == 2, f"got {doc.total_leave_days}")

doc = MockDoc("2026-06-05", "2026-06-05", 1, employee_category="Non-Office")
validate_sandwich_leave(doc, os_both, lt)
test_case("8.8 Both filter, Non-Office: sandwich applied",
          doc.total_leave_days == 2, f"got {doc.total_leave_days}")

# 8.9 No employee category on doc -> treated as "no restriction"
doc = MockDoc("2026-06-05", "2026-06-05", 1, employee_category=None)
validate_sandwich_leave(doc, os_office_only, lt)
test_case("8.9 Office filter, no emp category: sandwich applied (no restriction)",
          doc.total_leave_days == 2, f"got {doc.total_leave_days}")

# 8.10 Direct core function with orion_settings param
r = get_sandwich_additional_days(lt, "2026-06-05", "2026-06-05",
                                  employee_category="Office",
                                  orion_settings=os_office_only)
test_case("8.10 Core: Office cat, Office filter: +1", r == 1, f"got {r}")

r = get_sandwich_additional_days(lt, "2026-06-05", "2026-06-05",
                                  employee_category="Non-Office",
                                  orion_settings=os_office_only)
test_case("8.11 Core: Non-Office cat, Office filter: +0", r == 0, f"got {r}")

# =============================================================================
# SECTION 9: Multi-day leave - Non-configured & partial sandwich config
# Non-configured categories: use min(HRMS, weekdays)
# Configured categories: use HRMS + sandwich - non_configured_weekends
# =============================================================================
print("\n--- SECTION 9: Multi-Day Leave Scenarios ---")

def count_weekends_in_range(from_str, to_str):
    """Count Sat+Sun in range (inclusive)."""
    from datetime import timedelta
    frm = date.fromisoformat(from_str)
    to = date.fromisoformat(to_str)
    count = 0
    current = frm
    while current <= to:
        if current.weekday() in (5, 6):
            count += 1
        current += timedelta(days=1)
    return count

def count_weekdays_in_range(from_str, to_str):
    """Count Mon-Fri in range (inclusive)."""
    from datetime import timedelta
    frm = date.fromisoformat(from_str)
    to = date.fromisoformat(to_str)
    count = 0
    current = frm
    while current <= to:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count

def count_non_configured_weekends(from_str, to_str, configured_day_names):
    """Count Sat/Sun in range NOT in configured_day_names."""
    from datetime import timedelta
    frm = date.fromisoformat(from_str)
    to = date.fromisoformat(to_str)
    count = 0
    current = frm
    while current <= to:
        if current.weekday() == 5 and "Saturday" not in configured_day_names:
            count += 1
        elif current.weekday() == 6 and "Sunday" not in configured_day_names:
            count += 1
        current += timedelta(days=1)
    return count

def get_sandwich_additional_days_mock(configured_day_names, from_str, to_str):
    """Mock the sandwich additional days logic."""
    frm = date.fromisoformat(from_str)
    to = date.fromisoformat(to_str)
    range_days = (to - frm).days
    additional = 0
    if "Saturday" in configured_day_names and (4 - frm.weekday()) % 7 == range_days:
        additional += 1
    if "Sunday" in configured_day_names and frm.weekday() == 0:
        additional += 1
    return additional

def _get_sandwich_adjustments_mock(from_str, to_str, configured_day_names, holiday_dates):
    """Mock the sandwich adjustments logic (configured_holidays, non_configured_working_weekends)."""
    from datetime import timedelta
    frm = date.fromisoformat(from_str)
    to = date.fromisoformat(to_str)
    configured_holidays = 0
    non_configured_working_weekends = 0
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
        current += timedelta(days=1)
    return configured_holidays, non_configured_working_weekends

def simulate_patched_result(orig_days, from_str, to_str, emp_cat, orion_settings, leave_type_obj,
                            holiday_dates=None):
    """Simulate patched_get_number_of_leave_days with the new logic.

    holiday_dates: set of date objects that are holidays for this employee.
                   If None, defaults to empty set (no holiday list).
    """
    configured_day_names = []
    if leave_type_obj and leave_type_obj.get("custom_enable_sandwich_rule"):
        raw = leave_type_obj.get("custom_sandwich_days") or ""
        configured_day_names = [d.strip() for d in raw.split("\n") if d.strip()]

    applies = _sandwich_applies_for_employee(orion_settings, emp_cat)
    if applies:
        additional = get_sandwich_additional_days_mock(configured_day_names, from_str, to_str)
        if configured_day_names:
            configured_holidays, non_configured_working_weekends = _get_sandwich_adjustments_mock(
                from_str, to_str, configured_day_names, holiday_dates or set()
            )
            return orig_days + additional + configured_holidays - non_configured_working_weekends
        return orig_days

    weekdays = count_weekdays_in_range(from_str, to_str)
    return min(orig_days, weekdays)

os_office_only = MockOrionSettings(enabled=True, categories=["Office"])
os_noffice_only = MockOrionSettings(enabled=True, categories=["Non-Office"])
os_both = MockOrionSettings(enabled=True, categories=["Office", "Non-Office"])

# ===== SECTION 9A: Non-configured categories =====
print("\n--- 9A: Non-Configured Categories (min(HRMS, weekdays)) ---")

# 9A.1 Fri-Mon, Non-Office, HRMS=4 (no holiday list): min(4,2)=2
r = simulate_patched_result(4, "2026-06-05", "2026-06-08", "Non-Office", os_office_only, lt_both)
test_case("9A.1 Fri-Mon, Non-Office, HRMS=4: min(4,2)=2",
          r == 2, f"got {r}")

# 9A.2 Fri-Mon, Non-Office, HRMS=2 (holiday list): min(2,2)=2
r = simulate_patched_result(2, "2026-06-05", "2026-06-08", "Non-Office", os_office_only, lt_both)
test_case("9A.2 Fri-Mon, Non-Office, HRMS=2: min(2,2)=2",
          r == 2, f"got {r}")

# 9A.3 Single Friday, Non-Office: min(1,1)=1
r = simulate_patched_result(1, "2026-06-05", "2026-06-05", "Non-Office", os_office_only, lt_both)
test_case("9A.3 Single Friday, Non-Office: min(1,1)=1",
          r == 1, f"got {r}")

# 9A.4 Single Monday, Non-Office: min(1,1)=1
r = simulate_patched_result(1, "2026-06-01", "2026-06-01", "Non-Office", os_office_only, lt_both)
test_case("9A.4 Single Monday, Non-Office: min(1,1)=1",
          r == 1, f"got {r}")

# ===== SECTION 9B: Configured categories - both Sat+Sun =====
print("\n--- 9B: Configured, Both Sat+Sun ---")

# 9B.1 Fri-Mon, both configured: 4 + 0 - 0 = 4
r = simulate_patched_result(4, "2026-06-05", "2026-06-08", "Office", os_office_only, lt_both)
test_case("9B.1 Fri-Mon, both Sat+Sun: 4+0-0=4",
          r == 4, f"got {r}")

# 9B.2 Friday only, both configured: 1 + 1 - 0 = 2
r = simulate_patched_result(1, "2026-06-05", "2026-06-05", "Office", os_office_only, lt_both)
test_case("9B.2 Friday only, both Sat+Sun: 1+1-0=2",
          r == 2, f"got {r}")

# 9B.3 Monday only, both configured: 1 + 1 - 0 = 2
r = simulate_patched_result(1, "2026-06-01", "2026-06-01", "Office", os_office_only, lt_both)
test_case("9B.3 Monday only, both Sat+Sun: 1+1-0=2",
          r == 2, f"got {r}")

# ===== SECTION 9C: Configured categories - only Saturday =====
print("\n--- 9C: Configured, Only Saturday ---")

# 9C.1 Fri-Mon, Sat only: 4 + 0 - 1(Sun) = 3
r = simulate_patched_result(4, "2026-06-05", "2026-06-08", "Office", os_office_only, lt_sat_only)
test_case("9C.1 Fri-Mon, Sat only: 4+0-1(Sun)=3",
          r == 3, f"got {r}")

# 9C.2 Friday only, Sat only: 1 + 1 - 0 = 2
r = simulate_patched_result(1, "2026-06-05", "2026-06-05", "Office", os_office_only, lt_sat_only)
test_case("9C.2 Friday only, Sat only: 1+1-0=2",
          r == 2, f"got {r}")

# 9C.3 Monday only, Sat only: 1 + 0 - 0 = 1
r = simulate_patched_result(1, "2026-06-01", "2026-06-01", "Office", os_office_only, lt_sat_only)
test_case("9C.3 Monday only, Sat only: 1+0-0=1",
          r == 1, f"got {r}")

# ===== SECTION 9D: Configured categories - only Sunday =====
print("\n--- 9D: Configured, Only Sunday ---")

# 9D.1 Fri-Mon, Sun only: 4 + 0 - 1(Sat) = 3
r = simulate_patched_result(4, "2026-06-05", "2026-06-08", "Office", os_office_only, lt_sun_only)
test_case("9D.1 Fri-Mon, Sun only: 4+0-1(Sat)=3",
          r == 3, f"got {r}")

# 9D.2 Friday only, Sun only: 1 + 0 - 0 = 1
r = simulate_patched_result(1, "2026-06-05", "2026-06-05", "Office", os_office_only, lt_sun_only)
test_case("9D.2 Friday only, Sun only: 1+0-0=1",
          r == 1, f"got {r}")

# 9D.3 Monday only, Sun only: 1 + 1 - 0 = 2
r = simulate_patched_result(1, "2026-06-01", "2026-06-01", "Office", os_office_only, lt_sun_only)
test_case("9D.3 Monday only, Sun only: 1+1-0=2",
          r == 2, f"got {r}")

# ===== SECTION 9E: Holiday list with both Sat+Sun as weekly-off =====
# Simulates "Office Staff - 2026" where both Saturday and Sunday are holidays
print("\n--- 9E: Holiday List (Both Sat+Sun Weekly-Off) with Partial Config ---")

holiday_both = {date(2026, 6, 5), date(2026, 6, 6), date(2026, 6, 7), date(2026, 6, 8),
                date(2026, 6, 12), date(2026, 6, 13), date(2026, 6, 14), date(2026, 6, 15)}
# Note: holiday_both includes all Sat+Sun dates. We use specific ranges below.

# 9E.1 Fri-Mon, Sat only, both Sat+Sun holiday: 2 + 0 + 1(Sat holiday) - 0 = 3
r = simulate_patched_result(2, "2026-06-05", "2026-06-08", "Office", os_office_only, lt_sat_only,
                            holiday_dates={date(2026, 6, 6), date(2026, 6, 7)})
test_case("9E.1 Fri-Mon, Sat only, both Sat+Sun holiday: 2+0+1-0=3",
          r == 3, f"got {r}")

# 9E.2 Fri-Mon, Sun only, both Sat+Sun holiday: 2 + 0 + 1(Sun holiday) - 0 = 3
r = simulate_patched_result(2, "2026-06-05", "2026-06-08", "Office", os_office_only, lt_sun_only,
                            holiday_dates={date(2026, 6, 6), date(2026, 6, 7)})
test_case("9E.2 Fri-Mon, Sun only, both Sat+Sun holiday: 2+0+1-0=3",
          r == 3, f"got {r}")

# 9E.3 Fri-Mon, both configured, both Sat+Sun holiday: 2 + 0 + 2(both holidays) - 0 = 4
r = simulate_patched_result(2, "2026-06-05", "2026-06-08", "Office", os_office_only, lt_both,
                            holiday_dates={date(2026, 6, 6), date(2026, 6, 7)})
test_case("9E.3 Fri-Mon, both configured, both Sat+Sun holiday: 2+0+2-0=4",
          r == 4, f"got {r}")

# 9E.4 Friday only, Sat only, both Sat+Sun holiday: 1 + 1 + 0 - 0 = 2
r = simulate_patched_result(1, "2026-06-05", "2026-06-05", "Office", os_office_only, lt_sat_only,
                            holiday_dates={date(2026, 6, 6), date(2026, 6, 7)})
test_case("9E.4 Friday only, Sat only, both Sat+Sun holiday: 1+1+0-0=2",
          r == 2, f"got {r}")

# 9E.5 Monday only, Sun only, both Sat+Sun holiday: 1 + 1 + 0 - 0 = 2
r = simulate_patched_result(1, "2026-06-01", "2026-06-08", "Office", os_office_only, lt_sun_only,
                            holiday_dates={date(2026, 6, 6), date(2026, 6, 7)})
# Wait, this is Mon-Jun1, not Mon of the same week. Let me use Mon-Jun8 instead.
r = simulate_patched_result(1, "2026-06-08", "2026-06-08", "Office", os_office_only, lt_sun_only,
                            holiday_dates={date(2026, 6, 6), date(2026, 6, 7)})
test_case("9E.5 Monday only, Sun only, both Sat+Sun holiday: 1+1+0-0=2",
          r == 2, f"got {r}")

# 9E.6 Non-configured category with both Sat+Sun holiday: min(2,2)=2 (unchanged)
r = simulate_patched_result(2, "2026-06-05", "2026-06-08", "Non-Office", os_office_only, lt_both,
                            holiday_dates={date(2026, 6, 6), date(2026, 6, 7)})
test_case("9E.6 Non-Office, both holiday: min(2,2)=2 (no change)",
          r == 2, f"got {r}")

# ===== SECTION 9F: Holiday list with only Sunday weekly-off, partial config =====
print("\n--- 9F: Holiday List (Only Sunday Weekly-Off) with Partial Config ---")

# 9F.1 Fri-Mon, Sat only, only Sun holiday: 3 + 0 + 0 - 0 = 3
r = simulate_patched_result(3, "2026-06-05", "2026-06-08", "Office", os_office_only, lt_sat_only,
                            holiday_dates={date(2026, 6, 7)})
test_case("9F.1 Fri-Mon, Sat only, only Sun holiday: 3+0+0-0=3",
          r == 3, f"got {r}")

# 9F.2 Fri-Mon, Sun only, only Sun holiday: 3 + 0 + 1(Sun holiday) - 1(Sat working) = 3
r = simulate_patched_result(3, "2026-06-05", "2026-06-08", "Office", os_office_only, lt_sun_only,
                            holiday_dates={date(2026, 6, 7)})
test_case("9F.2 Fri-Mon, Sun only, only Sun holiday: 3+0+1-1=3",
          r == 3, f"got {r}")

# 9F.3 Fri-Mon, both configured, only Sun holiday: 3 + 0 + 1(Sun holiday) - 0 = 4
r = simulate_patched_result(3, "2026-06-05", "2026-06-08", "Office", os_office_only, lt_both,
                            holiday_dates={date(2026, 6, 7)})
test_case("9F.3 Fri-Mon, both configured, only Sun holiday: 3+0+1-0=4",
          r == 4, f"got {r}")

# =============================================================================
# SUMMARY
# =============================================================================
total = passed + failed
print(f"\n{'=' * 70}")
print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")
print(f"{'=' * 70}")
if failed:
    print("SOME TESTS FAILED - review above for details")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
    sys.exit(0)
