import frappe
import unittest
from frappe.utils import getdate, add_months, add_days, flt
from frappe.tests.utils import FrappeTestCase
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on


class TestExcessLeaveFunctionality(FrappeTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leave_type = frappe.get_doc("Leave Type", "ANNUAL LEAVE")
        cls.max_carry = flt(cls.leave_type.maximum_carry_forwarded_leaves or 15)

    def test_excess_leave_detection(self):
        from orion_erp.orion_erp.scripts.annual_leave_accrual import create_carry_forward

        employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
        if not employee:
            self.skipTest("No active employee found")

        emp_doc = frappe.get_doc("Employee", employee)
        doj = getdate(emp_doc.date_of_joining)

        balance = get_leave_balance_on(employee, "ANNUAL LEAVE", getdate())

        excess = max(0, balance - self.max_carry)
        print(f"Employee: {employee}, Balance: {balance}, Max Carry: {self.max_carry}, Excess: {excess}")

        carry_forward_allocs = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee,
                "leave_type": "ANNUAL LEAVE",
                "description": ["like", "%Carry Forward%"],
                "docstatus": 1
            },
            fields=["name", "custom_excess_leave_days"],
            order_by="creation desc",
            limit=1
        )

        if carry_forward_allocs:
            alloc = carry_forward_allocs[0]
            print(f"Found carry forward allocation: {alloc.name}, excess_days: {alloc.custom_excess_leave_days}")
            self.assertIsNotNone(alloc.custom_excess_leave_days)
            if excess > 0:
                self.assertGreater(flt(alloc.custom_excess_leave_days), 0)
        else:
            if excess > 0:
                print("No carry forward allocation found yet; excess leaves expected but not yet tracked")

    def test_excess_leave_report_query(self):
        from orion_erp.orion_erp.report.excess_leave_report.excess_leave_report import get_data

        data = get_data({})
        self.assertIsInstance(data, list)
        print(f"Excess Leave Report returned {len(data)} rows")

        for row in data:
            print(f"  {row.employee}: balance={row.current_balance}, limit={row.carry_over_limit}, excess={row.excess_days}, status={row.action_status}")

    def test_excess_leave_notification(self):
        from orion_erp.orion_erp.scripts.excess_leave_notification import get_hr_user_emails

        emails = get_hr_user_emails()
        self.assertIsInstance(emails, list)
        print(f"HR user emails: {emails}")

    def test_excess_leave_custom_fields(self):
        meta = frappe.get_meta("Leave Allocation")
        fields = ["custom_excess_leave_days", "custom_excess_leave_status",
                   "custom_carry_forward_days", "custom_decision_date",
                   "custom_decided_by", "custom_excess_leave_remarks"]

        for field in fields:
            df = meta.get_field(field)
            self.assertIsNotNone(df, f"Field {field} not found on Leave Allocation")
            print(f"Field {field}: type={df.fieldtype}, exists=True")


if __name__ == "__main__":
    unittest.main()
