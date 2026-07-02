# Copyright (c) 2026, osama.ahmed@deliverydevs.com and Contributors
# See license.txt

from datetime import date, timedelta

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLEAVEDECLARATION(FrappeTestCase):

    def setUp(self):
        frappe.db.savepoint("test_leave_declaration")
        self.company = frappe.get_all("Company", pluck="name", limit=1)[0]
        self.leave_type = frappe.get_all("Leave Type", pluck="name", limit=1)[0]
        self.holiday_list = frappe.get_all("Holiday List", pluck="name", limit=1)
        if not self.holiday_list:
            self.fail("No Holiday List found in the database")

    def tearDown(self):
        frappe.db.rollback(save_point="test_leave_declaration")

    def _get_employee(self):
        emp_name = frappe.get_all("Employee", filters={"status": "Active", "holiday_list": ["!=", ""]}, pluck="name", limit=1)
        if not emp_name:
            self.fail("No active employee with holiday_list found in the database")
        return emp_name[0]

    def _create_leave_declaration(self, employee, start, end, rejoining_date=None):
        emp_name = frappe.db.get_value("Employee", employee, "employee_name")
        ld = frappe.get_doc({
            "doctype": "LEAVE DECLARATION",
            "employee": employee,
            "employee_name": emp_name,
            "company": self.company,
            "passport_number": "TEST123",
            "data": "Test",
            "leave_type": self.leave_type,
            "leaving_date": str(start),
            "leave_start_date": str(start),
            "leave_end_date": str(end),
            "rejoining_date": str(rejoining_date) if rejoining_date else None
        })
        ld.flags.ignore_permissions = True
        return ld

    def _create_leave_application(self, employee, start, end):
        la = frappe.get_doc({
            "doctype": "Leave Application",
            "employee": employee,
            "leave_type": self.leave_type,
            "from_date": str(start),
            "to_date": str(end),
            "company": self.company,
            "status": "Approved",
            "custom_approval_status": "Open",
            "leave_approver": "Administrator"
        })
        la.flags.ignore_permissions = True
        la.insert()
        la.submit()
        return la

    def test_create_leave_application_when_no_existing(self):
        emp = self._get_employee()
        start = date.today() + timedelta(days=10)
        end = start + timedelta(days=5)

        ld = self._create_leave_declaration(emp, start, end)
        ld.insert()
        ld.submit()

        self.assertTrue(ld.created_leave_application)
        self.assertTrue(
            frappe.db.exists("Leave Application", ld.created_leave_application)
        )

        la = frappe.get_doc("Leave Application", ld.created_leave_application)
        self.assertEqual(la.employee, emp)
        self.assertEqual(la.leave_type, self.leave_type)
        self.assertEqual(str(la.from_date), str(start))
        self.assertEqual(str(la.to_date), str(end))

    def test_no_new_la_when_existing_covers_same_period(self):
        emp = self._get_employee()
        start = date.today() + timedelta(days=20)
        end = start + timedelta(days=5)

        existing_la = self._create_leave_application(emp, start, end)

        ld = self._create_leave_declaration(emp, start, end)
        ld.insert()
        ld.submit()

        self.assertFalse(ld.created_leave_application)

    def test_rejoining_same_date_adjusts_leave_end(self):
        emp = self._get_employee()
        start = date.today() + timedelta(days=30)
        end = start + timedelta(days=10)

        existing_la = self._create_leave_application(emp, start, end)

        ld = self._create_leave_declaration(emp, start, end, rejoining_date=end)
        ld.insert()
        ld.submit()

        self.assertTrue(ld.created_leave_application)
        self.assertNotEqual(ld.created_leave_application, existing_la.name)
        self.assertEqual(
            frappe.db.get_value("Leave Application", existing_la.name, "docstatus"),
            2
        )
        new_la = frappe.get_doc("Leave Application", ld.created_leave_application)
        last_leave_day = end - timedelta(days=1)
        self.assertEqual(str(new_la.to_date), str(last_leave_day))

    def test_early_return_cancels_and_creates_new(self):
        emp = self._get_employee()
        start = date.today() + timedelta(days=40)
        end = start + timedelta(days=10)
        rejoining = start + timedelta(days=5)

        existing_la = self._create_leave_application(emp, start, end)

        ld = self._create_leave_declaration(emp, start, end, rejoining_date=rejoining)
        ld.insert()
        ld.submit()

        self.assertTrue(ld.created_leave_application)
        self.assertNotEqual(ld.created_leave_application, existing_la.name)
        self.assertEqual(
            frappe.db.get_value("Leave Application", existing_la.name, "docstatus"),
            2
        )

        new_la = frappe.get_doc("Leave Application", ld.created_leave_application)
        self.assertEqual(str(new_la.from_date), str(start))
        last_leave_day = rejoining - timedelta(days=1)
        self.assertEqual(str(new_la.to_date), str(last_leave_day))

    def test_late_return_creates_base_la_only(self):
        emp = self._get_employee()
        start = date.today() + timedelta(days=50)
        end = start + timedelta(days=5)

        ld = self._create_leave_declaration(emp, start, end, rejoining_date=end + timedelta(days=10))
        ld.insert()
        ld.submit()

        self.assertTrue(ld.created_leave_application)
        self.assertFalse(ld.extended_leave_application)

        la = frappe.get_doc("Leave Application", ld.created_leave_application)
        self.assertEqual(str(la.from_date), str(start))
        self.assertEqual(str(la.to_date), str(end))
