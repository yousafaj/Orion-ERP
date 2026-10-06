"""An allocation edit must not repost credits from a different company."""

import sys
import types
import unittest
from unittest.mock import patch

import test_leave_projection_standalone as helpers


class OfficeAllocationTests(unittest.TestCase):
    def setUp(self):
        fixture = helpers.BalanceTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.frappe = fixture.frappe
        self.category = "Office"
        self.frappe.db.get_value = lambda *args: self.category
        native = types.ModuleType("hrms.hr.doctype.leave_allocation.leave_allocation")
        class Native:
            def get_existing_leave_count(self):
                return 123.0
        native.LeaveAllocation = Native
        modules = patch.dict(sys.modules, {
            "hrms.hr.doctype.leave_allocation.leave_allocation": native,
            "orion_erp.orion_erp.overrides.leave_application": fixture.controller,
        })
        modules.start()
        self.addCleanup(modules.stop)
        self.controller = helpers.load("office_allocation", "orion_erp/orion_erp/overrides/leave_allocation.py")
        self.doc = self.controller.OrionLeaveAllocation()
        self.doc.name, self.doc.employee, self.doc.leave_type = "ALLOC", "EMP", "ANNUAL"
        self.rows = []
        def get_all(doctype, filters, fields):
            selected = [row for row in self.rows if all(row.get(k) == v for k, v in filters.items())]
            return [helpers.Row(total_leaves=sum(row["leaves"] for row in selected))]
        self.frappe.get_all = get_all

    def row(self, leaves, company="OLD", **changes):
        self.rows.append(dict(transaction_type="Leave Allocation", transaction_name="ALLOC",
            employee="EMP", leave_type="ANNUAL", is_carry_forward=0, docstatus=1,
            company=company, leaves=leaves, **changes))

    def test_mixed_company_adjustment_uses_net_credits(self):
        self.row(20)
        self.row(2.5, "NEW")
        self.row(2.5, "NEW")
        self.assertEqual(27.5 - self.doc.get_existing_leave_count(), 2.5)

    def test_compensating_negative_entry_counts(self):
        self.row(20)
        self.row(2.5, "NEW")
        self.row(2.5, "NEW")
        self.row(7.5, "NEW")
        self.row(-5, "NEW")
        self.assertEqual(self.doc.get_existing_leave_count(), 27.5)
        self.assertEqual(30 - self.doc.get_existing_leave_count(), 2.5)

    def test_unrelated_cancelled_and_carry_forward_entries_do_not_count(self):
        self.row(10)
        for field, value in [("transaction_name", "OTHER"), ("employee", "OTHER"),
                ("leave_type", "OTHER"), ("transaction_type", "Leave Application"),
                ("docstatus", 2), ("docstatus", 0), ("is_carry_forward", 1)]:
            row = dict(self.rows[0], leaves=100)
            row[field] = value
            self.rows.append(row)
        self.assertEqual(self.doc.get_existing_leave_count(), 10)

    def test_native_expiry_semantics_are_preserved(self):
        self.row(10)
        self.row(-10, is_expired=1)
        self.assertEqual(self.doc.get_existing_leave_count(), 0)

    def test_no_credits_is_zero(self):
        self.assertEqual(self.doc.get_existing_leave_count(), 0)

    def test_non_office_keeps_native_behavior(self):
        self.category = "Non-Office"
        self.assertEqual(self.doc.get_existing_leave_count(), 123)

    def test_other_leave_type_keeps_native_behavior(self):
        self.doc.leave_type = "SICK"
        self.assertEqual(self.doc.get_existing_leave_count(), 123)


if __name__ == "__main__":
    unittest.main()
