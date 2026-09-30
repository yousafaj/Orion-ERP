"""Business-rule regression tests, runnable without a Frappe database.

Run: python -m unittest discover -s tests -p 'test_leave_projection_standalone.py'
"""
import importlib.util
import sys
import types
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


projection = load("forecast", "orion_erp/orion_erp/services/leave_projection.py")
RULES = [dict(from_months=0, to_months=6, days_per_month=2),
         dict(from_months=6, to_months=12, days_per_month=2.5),
         dict(from_months=12, to_months=0, days_per_month=2.5)]


class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class Rejected(Exception):
    pass


def throw(message, **kwargs):
    raise kwargs.get("exc", Rejected)(message)


class ForecastTests(unittest.TestCase):
    def forecast(self, joining, today, start, end=date(2027, 3, 22)):
        return projection.project_accrual(joining, today, start, RULES, joining, end)

    def test_employee_250_december_credit_dates(self):
        joining, today = date(2022, 3, 22), date(2026, 9, 30)
        self.assertEqual(self.forecast(joining, today, date(2026, 12, 1)), 5)
        self.assertEqual(self.forecast(joining, today, date(2026, 12, 22)), 7.5)

    def test_no_credit_today_or_past(self):
        joining, today = date(2025, 10, 27), date(2026, 9, 27)
        self.assertEqual(self.forecast(joining, today, today), 0)
        self.assertEqual(self.forecast(joining, today, date(2026, 9, 26)), 0)
        self.assertEqual(self.forecast(joining, today, date(2026, 10, 27)), 2.5)

    def test_end_of_month_and_leap_day(self):
        self.assertEqual(projection.anniversary(date(2024, 1, 31), 1), date(2024, 2, 29))
        self.assertEqual(projection.anniversary(date(2024, 2, 29), 12), date(2025, 2, 28))

    def test_sixth_month_matches_scheduler_without_catchup(self):
        self.assertEqual(self.forecast(date(2026, 1, 31), date(2026, 6, 30), date(2026, 7, 31)), 2)

    def test_no_credit_after_allocation_expiry(self):
        self.assertEqual(self.forecast(date(2022, 3, 22), date(2026, 9, 30),
                                       date(2026, 12, 22), date(2026, 10, 22)), 2.5)


class BalanceTests(unittest.TestCase):
    def setUp(self):
        frappe = types.ModuleType("frappe")
        utils = types.ModuleType("frappe.utils")
        utils.getdate = lambda value=None: date.fromisoformat(value) if isinstance(value, str) else (value or date(2026, 9, 30))
        utils.flt = lambda value, precision=None: round(float(value or 0), precision) if precision is not None else float(value or 0)
        utils.cint = lambda value: int(value or 0)
        utils.date_diff = lambda end, start: (utils.getdate(end) - utils.getdate(start)).days
        utils.now_datetime = lambda: None
        utils.add_days = lambda *args: None
        utils.add_months = lambda *args: None
        frappe._ = lambda value: value
        frappe._dict = Row
        frappe.throw = throw
        frappe.whitelist = lambda *args, **kwargs: lambda function: function
        frappe.validate_and_sanitize_search_inputs = lambda function: function
        frappe.db = Row(get_value=lambda *args: date(2022, 3, 22), sql=lambda *args: [])
        self.settings = Row(leave_types_for_accrual=[Row(leave_type="ANNUAL")],
                            leave_types_requiring_one_year_service=[Row(leave_type="ANNUAL")])
        frappe.get_cached_doc = lambda doctype, *args: self.settings if doctype == "Orion Settings" else Row(custom_annual_leave_accrual_rules=[Row(r) for r in RULES])
        frappe.get_single = lambda *args: self.settings
        self.pending = []
        self.entries = []
        self.allocations = [Row(name="ALLOC", from_date=date(2022, 3, 22), to_date=date(2027, 3, 22))]
        frappe.get_all = lambda doctype, **kwargs: {"Leave Allocation": self.allocations,
            "Leave Application": self.pending, "Leave Ledger Entry": self.entries}[doctype]
        standard = types.ModuleType("hrms.hr.doctype.leave_application.leave_application")
        class Native:
            def validate_balance_leaves(self):
                self.native_called = True
        standard.LeaveApplication = Native
        standard.InsufficientLeaveBalanceError = Rejected
        self.native_balance = 34.5
        standard.get_leave_balance_on = lambda *args, **kwargs: Row(leave_balance=self.native_balance, leave_balance_for_consumption=self.native_balance) if kwargs.get("for_consumption") else 34.5
        self.native_allocation = Row(from_date=date(2022, 3, 22), unused_leaves=0)
        standard.get_leave_allocation_records = lambda *args: {"ANNUAL": self.native_allocation}
        standard.get_allocation_expiry_for_cf_leaves = lambda *args: date(2026, 12, 2)
        standard.get_new_and_cf_leaves_taken = lambda *args: (0, 0)
        standard.get_number_of_leave_days = lambda *args: 40
        standard.validate_leave_access = lambda *args: None
        package = types.ModuleType("hrms.hr.doctype.leave_application")
        package.leave_application = standard
        self.modules = patch.dict(sys.modules, {"frappe": frappe, "frappe.utils": utils,
            "hrms.hr.doctype.leave_application": package,
            "hrms.hr.doctype.leave_application.leave_application": standard,
            "orion_erp.orion_erp.services.leave_projection": projection})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.controller = load("balance", "orion_erp/orion_erp/overrides/leave_application.py")
        self.frappe = frappe

    def summary(self, application=None):
        return self.controller.balance_summary("EMP", "ANNUAL", "2026-12-01", "2027-01-09", application)

    def test_future_balance_is_exact_not_rounded_up(self):
        summary = self.summary()
        self.assertEqual(summary.current_balance, 34.5)
        self.assertEqual(summary.projected_balance, 39.5)

    def test_pending_reserved_self_and_rejected_excluded(self):
        self.pending = [Row(name="OTHER", total_leave_days=4), Row(name="SELF", total_leave_days=6),
                        Row(name="REJECTED", total_leave_days=9, workflow_state="Rejected"),
                        Row(name="ORION-REJECTED", total_leave_days=10, custom_approval_status="Rejected")]
        self.assertEqual(self.summary("SELF").projected_balance, 35.5)

    def test_submitted_request_not_charged_twice(self):
        self.native_balance = 24.5
        self.entries = [Row(leaves=-10)]
        self.assertEqual(self.summary("SELF").projected_balance, 39.5)

    def test_missing_or_cross_period_allocation_fails(self):
        self.allocations = []
        with self.assertRaises(Rejected):
            self.summary()

    def test_reserve_before_allocation_calendar_cap(self):
        self.allocations[0].to_date = date(2026, 12, 5)
        self.pending = [Row(name="OTHER", total_leave_days=4)]
        summary = self.controller.balance_summary("EMP", "ANNUAL", "2026-12-01", "2026-12-05")
        self.assertEqual(summary.projected_balance, 5)

    def test_carry_forward_expiry_cap_preserved(self):
        self.native_allocation.unused_leaves = 10
        self.assertEqual(self.summary().projected_balance, 31.5)

    def doc(self, leave_type="ANNUAL", status="Open"):
        doc = self.controller.OrionLeaveApplication()
        for field, value in dict(employee="EMP", leave_type=leave_type, status=status, docstatus=0,
                from_date="2026-12-01", to_date="2027-01-09", half_day=0, half_day_date=None, name="SELF").items():
            setattr(doc, field, value)
        doc.is_new = lambda: True
        doc.get = lambda key: getattr(doc, key, None)
        return doc

    def test_excess_blocked_even_when_native_type_allows_negative(self):
        with self.assertRaises(Rejected):
            self.doc().validate_balance_leaves()
        self.native_balance = 35
        doc = self.doc()
        doc.validate_balance_leaves()
        self.assertEqual(doc.leave_balance, 40)

    def test_other_leave_uses_native_validation(self):
        doc = self.doc("SICK")
        doc.validate_balance_leaves()
        self.assertTrue(doc.native_called)

    def test_rejection_not_blocked_by_expired_allocation(self):
        self.allocations = []
        validations = load("validations", "orion_erp/orion_erp/validations/leave_application.py")
        with patch.dict(sys.modules, {"orion_erp.orion_erp.validations.leave_application": validations}):
            doc = self.doc(status="Rejected")
            doc.is_new = lambda: False
            doc.validate_balance_leaves()
            doc.status = "Open"
            doc.leave_approver = "MANAGER"
            doc.custom_initial_approver_status = "Cancelled"
            doc.validate_balance_leaves()

    def test_new_rejected_status_cannot_bypass_balance_guard(self):
        with self.assertRaises(Rejected):
            self.doc(status="Rejected").validate_balance_leaves()

    def test_under_one_year_annual_request_has_no_blanket_warning(self):
        validations = load("eligibility", "orion_erp/orion_erp/validations/leave_application/eligibility.py")
        self.frappe.db.get_value = lambda *args: date(2025, 10, 27)
        doc = Row(employee="EMP", leave_type="ANNUAL", from_date="2026-09-24",
                  custom_eligibility_warnings="You must complete 1 year of service to apply for ANNUAL.\nOther review")
        validations.validate_annual_leave_avail(doc)
        self.assertEqual(doc.custom_eligibility_warnings, "Other review")
        doc.from_date = "2026-03-24"
        validations.validate_annual_leave_avail(doc)
        self.assertIn("requires HR and management review", doc.custom_eligibility_warnings)


if __name__ == "__main__":
    unittest.main()
