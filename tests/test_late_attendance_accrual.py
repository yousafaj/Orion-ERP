"""Late attendance must earn one credit, without duplicating imported totals."""
import sys
import types
import unittest
from datetime import date
from unittest.mock import patch

import test_leave_projection_standalone as helpers

Row, load, projection, RULES = helpers.Row, helpers.load, helpers.projection, helpers.RULES


class LateAttendanceTests(unittest.TestCase):
    def setUp(self):
        fixture = helpers.BalanceTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        frappe = fixture.frappe
        utils = sys.modules["frappe.utils"]
        utils.add_months = lambda value, n: projection.anniversary(utils.getdate(value), n)
        self.allocation = Row(name="ALLOC", employee="EMP", leave_type="ANNUAL",
            from_date=date(2025, 10, 27), to_date=date(2026, 10, 26), expired=0,
            modified=date(2026, 8, 27), new_leaves_allocated=22.5, total_leaves_allocated=22.5,
            company="COMPANY", description="Month 10 | Allocated: 2.5 days (27 July 2026 - 26 August 2026)")
        self.attendance = True
        self.ledgers = []
        self.locks = []
        def sql(query, values, **kwargs):
            if "FOR UPDATE" in query:
                self.locks.append(values)
                return []
            description = values[2].strip("%")
            return ["ALLOC"] if description in self.allocation.description else []
        def get_value(doctype, name, fields=None, **kwargs):
            if doctype == "Employee":
                return Row(status="Active", date_of_joining=date(2025, 10, 27))
            return self.allocation if isinstance(fields, list) else self.allocation.get(fields)
        def set_value(doctype, name, field, value=None):
            if isinstance(field, dict):
                self.allocation.update(field)
            else:
                self.allocation[field] = value
        frappe.db = Row(sql=sql, get_value=get_value, set_value=set_value,
            exists=lambda doctype, filters: self.attendance if doctype == "Attendance" else "ALLOC")
        frappe.get_all = lambda *args, **kwargs: [self.allocation]
        frappe.get_cached_doc = lambda *args: Row(custom_annual_leave_accrual_rules=[Row(r) for r in RULES])
        def get_doc(data):
            ledger = Row(data, flags=Row())
            ledger.submit = lambda: self.ledgers.append(data)
            return ledger
        frappe.get_doc = get_doc
        ledger_module = types.ModuleType("hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry")
        ledger_module.expire_allocation = lambda *args: None
        ledger_module.get_remaining_leaves = lambda *args: 0
        notify = types.ModuleType("orion_erp.orion_erp.scripts.excess_leave_notification")
        notify.notify_excess_leaves = lambda *args: None
        modules = patch.dict(sys.modules, {
            "hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry": ledger_module,
            "orion_erp.orion_erp.scripts.excess_leave_notification": notify})
        modules.start()
        self.addCleanup(modules.stop)
        self.accrual = load("accrual", "orion_erp/orion_erp/scripts/annual_leave_accrual.py")

    def run_accrual(self):
        self.accrual.reconcile_employee_accrual("EMP", ["ANNUAL"])

    def test_september_credit_after_anniversary_and_idempotent_retry(self):
        self.run_accrual()
        self.run_accrual()
        self.assertEqual(self.allocation.total_leaves_allocated, 25)
        self.assertEqual(len(self.ledgers), 1)
        self.assertEqual(self.ledgers[0]["leaves"], 2.5)
        self.assertIn("Month 11 | Allocated: 2.5 days", self.allocation.description)
        self.assertEqual(len(self.locks), 2)

    def test_no_credit_until_submitted_attendance_exists(self):
        self.attendance = False
        self.run_accrual()
        self.assertEqual(self.allocation.total_leaves_allocated, 22.5)
        self.attendance = True
        self.run_accrual()
        self.assertEqual(self.allocation.total_leaves_allocated, 25)

    def test_rule_change_does_not_credit_the_same_month_twice(self):
        self.run_accrual()
        self.accrual.get_rules_from_leave_type = lambda *args: [dict(from_months=0, to_months=0, days_per_month=3)]
        self.run_accrual()
        self.assertEqual(self.allocation.total_leaves_allocated, 25)
        self.assertEqual(len(self.ledgers), 1)

    def test_expired_year_is_not_reopened(self):
        self.allocation.expired = 1
        self.run_accrual()
        self.assertEqual(self.allocation.total_leaves_allocated, 22.5)
        self.assertEqual(self.ledgers, [])

    def test_manual_opening_balance_is_not_recredited(self):
        self.allocation.description = "Imported opening balance"
        self.allocation.modified = date(2026, 9, 30)
        self.run_accrual()
        self.assertEqual(self.allocation.total_leaves_allocated, 22.5)
        self.assertEqual(self.ledgers, [])
