# Copyright (c) 2026, osama.ahmed@deliverydevs.com and Contributors
# See license.txt

import time
import random
from datetime import date, timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from orion_erp.orion_erp.doctype.leave_declaration.leave_declaration import (
    get_available_leave_applications,
    get_leave_application_data,
    get_employee_asset_details,
)


class TestLEAVEDECLARATION(FrappeTestCase):

    def setUp(self):
        self.company = frappe.get_all("Company", pluck="name", limit=1)[0]
        self.leave_type = "ANNUAL LEAVE"
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        test_lds = frappe.get_all("LEAVE DECLARATION", filters={"name": ["like", "HR/LD/%"]}, pluck="name")
        for ld_name in test_lds:
            try:
                frappe.delete_doc("LEAVE DECLARATION", ld_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        test_las = frappe.get_all("Leave Application", filters={"name": ["like", "TEST-LA-%"]}, pluck="name")
        for la_name in test_las:
            try:
                frappe.delete_doc("Leave Application", la_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        frappe.db.commit()

    def _get_employee_with_allocation(self):
        emp = frappe.get_all(
            "Employee",
            filters={"status": "Active", "holiday_list": ["!=", ""]},
            pluck="name",
            limit=1,
        )
        if not emp:
            self.fail("No active employee with holiday_list found")
        employee = emp[0]

        alloc = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee,
                "leave_type": self.leave_type,
                "docstatus": 1,
            },
            fields=["from_date", "to_date"],
            limit=1,
        )
        if not alloc:
            self.fail(f"No Leave Allocation for {self.leave_type}")

        return employee, alloc[0].from_date, alloc[0].to_date

    def _get_free_dates(self, employee, alloc_start, alloc_end, count=1, gap=3):
        existing_dates = set(
            frappe.get_all(
                "Attendance",
                filters={"employee": employee, "docstatus": 1},
                pluck="attendance_date",
            )
        )
        existing_la_dates = set(
            frappe.get_all(
                "Leave Application",
                filters={"employee": employee, "docstatus": ["!=", 2]},
                pluck="from_date",
            )
        )
        blocked = existing_dates | existing_la_dates

        results = []
        current = alloc_start
        while current <= alloc_end and len(results) < count:
            if current not in blocked:
                results.append(current)
            current += timedelta(days=gap)

        if not results:
            fallback = alloc_end - timedelta(days=4)
            while fallback >= alloc_start and len(results) < count:
                if fallback not in blocked:
                    results.append(fallback)
                fallback -= timedelta(days=1)

        return results

    def _clear_attendance_for_range(self, employee, start, end):
        frappe.db.sql(
            """DELETE FROM `tabAttendance`
            WHERE employee = %s AND attendance_date BETWEEN %s AND %s AND docstatus = 1""",
            (employee, str(start), str(end)),
        )
        frappe.db.commit()

    def _create_approved_leave_application(self, employee, start, end):
        self._clear_attendance_for_range(employee, start, end)

        la_name = f"TEST-LA-TD-{int(time.time()*1000)}-{random.randint(100,999)}"
        frappe.db.sql(
            """INSERT INTO `tabLeave Application`
            (name, employee, employee_name, leave_type, from_date, to_date, company,
             status, custom_approval_status, docstatus, leave_approver, posting_date,
             creation, modified, owner, modified_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'Administrator', CURDATE(), NOW(), NOW(), 'Administrator', 'Administrator')""",
            (
                la_name, employee,
                frappe.db.get_value("Employee", employee, "employee_name"),
                self.leave_type, str(start), str(end), self.company,
                "Approved", "Approved",
            ),
        )
        frappe.db.commit()
        return frappe.get_doc("Leave Application", la_name)

    def _create_leave_declaration(self, employee, leave_application, start, end):
        emp_name = frappe.db.get_value("Employee", employee, "employee_name")
        rejoining = end + timedelta(days=1)
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
            "rejoining_date": str(rejoining),
            "leave_application": leave_application,
        })
        ld.flags.ignore_permissions = True
        return ld

    def test_leave_application_fetches_data(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=3)
        if not dates:
            self.fail("No free dates")
        start = dates[0]
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)
        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.insert()

        self.assertEqual(ld.employee, la.employee)
        self.assertEqual(ld.employee_name, la.employee_name)
        self.assertEqual(ld.company, la.company)
        self.assertEqual(ld.leave_type, la.leave_type)
        self.assertEqual(str(ld.leave_start_date), str(la.from_date))
        self.assertEqual(str(ld.leave_end_date), str(la.to_date))
        self.assertEqual(str(ld.leaving_date), str(la.from_date))

    def test_submit_links_leave_application(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=6)
        if not dates:
            self.fail("No free dates")
        start = dates[0]
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)
        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.insert()
        ld.submit()

        self.assertEqual(
            frappe.db.get_value("Leave Application", la.name, "custom_leave_declaration"),
            ld.name,
        )

    def test_cancel_unlinks_leave_application(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        today = getdate()
        if today + timedelta(days=5) > alloc_end:
            self.skipTest("Not enough allocation time in the future for cancel test")
        start = today + timedelta(days=3)
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)
        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.insert()
        ld.submit()
        ld.cancel()

        self.assertIsNone(
            frappe.db.get_value("Leave Application", la.name, "custom_leave_declaration")
        )

    def test_duplicate_leave_application_blocked(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=12)
        if not dates:
            self.fail("No free dates")
        start = dates[0]
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)
        ld1 = self._create_leave_declaration(emp, la.name, start, end)
        ld1.insert()
        ld1.submit()

        ld2 = self._create_leave_declaration(emp, la.name, start, end)
        with self.assertRaises(frappe.exceptions.ValidationError):
            ld2.insert()

    def test_available_leave_applications_excludes_used(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=15)
        if not dates:
            self.fail("No free dates")
        start = dates[0]
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)
        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.insert()
        ld.submit()

        available = get_available_leave_applications(
            "Leave Application", "", "name", 0, 100,
            {"employee": emp}
        )
        available_names = [a[0] for a in available]
        self.assertNotIn(la.name, available_names)

    def test_available_leave_applications_includes_approved_unused(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=18)
        if not dates:
            self.fail("No free dates")
        start = dates[0]
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)

        available = get_available_leave_applications(
            "Leave Application", "", "name", 0, 100,
            {"employee": emp}
        )
        available_names = [a[0] for a in available]
        self.assertIn(la.name, available_names)

    def test_available_excludes_non_approved(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=21)
        if not dates:
            self.fail("No free dates")
        start = dates[0]
        end = start + timedelta(days=3)

        self._clear_attendance_for_range(emp, start, end)

        la_name = f"TEST-LA-TD-{int(time.time()*1000)}-{random.randint(100,999)}"
        frappe.db.sql(
            """INSERT INTO `tabLeave Application`
            (name, employee, employee_name, leave_type, from_date, to_date, company,
             status, custom_approval_status, docstatus, leave_approver, posting_date,
             creation, modified, owner, modified_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 'Administrator', CURDATE(), NOW(), NOW(), 'Administrator', 'Administrator')""",
            (
                la_name, emp,
                frappe.db.get_value("Employee", emp, "employee_name"),
                self.leave_type, str(start), str(end), self.company,
                "Open", "Open",
            ),
        )
        frappe.db.commit()
        la = frappe.get_doc("Leave Application", la_name)

        available = get_available_leave_applications(
            "Leave Application", "", "name", 0, 100,
            {"employee": emp}
        )
        available_names = [a[0] for a in available]
        self.assertNotIn(la.name, available_names)

    def test_get_leave_application_data(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=24)
        if not dates:
            self.fail("No free dates")
        start = dates[0]
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)
        data = get_leave_application_data(la.name)

        self.assertEqual(data["employee"], la.employee)
        self.assertEqual(data["employee_name"], la.employee_name)
        self.assertEqual(data["company"], la.company)
        self.assertEqual(data["leave_type"], la.leave_type)
        self.assertEqual(str(data["leave_start_date"]), str(la.from_date))
        self.assertEqual(str(data["leave_end_date"]), str(la.to_date))
        self.assertIsNotNone(data["designation"])

    def test_no_la_generation_on_submit(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=27)
        if not dates:
            self.fail("No free dates")
        start = dates[0]
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)
        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.insert()

        la_count_before = frappe.db.count("Leave Application")
        ld.submit()
        la_count_after = frappe.db.count("Leave Application")

        self.assertEqual(la_count_before, la_count_after)

    def test_remark_field_saved(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=30)
        if not dates:
            self.fail("No free dates")
        start = dates[0]
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)
        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.remark = "Test remark for leave declaration"
        ld.insert()

        saved = frappe.get_doc("LEAVE DECLARATION", ld.name)
        self.assertEqual(saved.remark, "Test remark for leave declaration")

    def test_asset_fetch_on_validate(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=33)
        start = dates[0]
        end = start + timedelta(days=3)

        la = self._create_approved_leave_application(emp, start, end)
        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.insert()

        assets = get_employee_asset_details(emp)
        self.assertIsInstance(ld.asset_clearance_detail, list)
        if assets:
            self.assertGreater(len(ld.asset_clearance_detail), 0)
            for row in ld.asset_clearance_detail:
                self.assertEqual(row.asset_status, "Active")

    def test_submit_updates_asset_status_to_returned(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=36)
        start = dates[0]
        end = start + timedelta(days=3)

        assets = get_employee_asset_details(emp)
        if not assets:
            self.skipTest("No active assets for employee")

        first_asset_name = assets[0].get("name")
        original_status = frappe.db.get_value("Asset Handover Detail", first_asset_name, "asset_status")
        self.assertEqual(original_status, "Active")

        la = self._create_approved_leave_application(emp, start, end)
        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.insert()

        for row in ld.asset_clearance_detail:
            if row.source_asset_handover_detail == first_asset_name:
                row.asset_status = "Returned"
                row.return_date = start
        ld.save()
        ld.submit()

        new_status = frappe.db.get_value("Asset Handover Detail", first_asset_name, "asset_status")
        self.assertEqual(new_status, "Returned")

    def test_cancel_reverses_asset_status_to_active(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        today = getdate()
        if today + timedelta(days=45) > alloc_end:
            self.skipTest("Not enough allocation time in the future for cancel test")
        start = today + timedelta(days=39)
        end = start + timedelta(days=3)

        assets = get_employee_asset_details(emp)
        if not assets:
            self.skipTest("No active assets for employee")

        first_asset_name = assets[0].get("name")

        la = self._create_approved_leave_application(emp, start, end)
        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.insert()

        for row in ld.asset_clearance_detail:
            if row.source_asset_handover_detail == first_asset_name:
                row.asset_status = "Returned"
                row.return_date = start
        ld.save()
        ld.submit()

        status_after_submit = frappe.db.get_value("Asset Handover Detail", first_asset_name, "asset_status")
        self.assertEqual(status_after_submit, "Returned")

        ld.cancel()

        status_after_cancel = frappe.db.get_value("Asset Handover Detail", first_asset_name, "asset_status")
        self.assertEqual(status_after_cancel, "Active")

    def test_unpaid_leave_type_blocked(self):
        emp, alloc_start, alloc_end = self._get_employee_with_allocation()
        unpaid_type = frappe.db.get_value("Leave Type", {"is_lwp": 1}, "name")
        if not unpaid_type:
            self.skipTest("No unpaid leave type found")

        dates = self._get_free_dates(emp, alloc_start, alloc_end, count=1, gap=42)
        if not dates:
            start = alloc_end - timedelta(days=1)
            end = alloc_end
        else:
            start = dates[0]
            end = start + timedelta(days=1)

        self._clear_attendance_for_range(emp, start, end)
        la_name = f"TEST-LA-UP-{int(time.time()*1000)}-{random.randint(100,999)}"
        frappe.db.sql(
            """INSERT INTO `tabLeave Application`
            (name, employee, employee_name, leave_type, from_date, to_date, company,
             status, custom_approval_status, docstatus, leave_approver, posting_date,
             creation, modified, owner, modified_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'Administrator', CURDATE(), NOW(), NOW(), 'Administrator', 'Administrator')""",
            (
                la_name, emp,
                frappe.db.get_value("Employee", emp, "employee_name"),
                self.leave_type, str(start), str(end), self.company,
                "Approved", "Approved",
            ),
        )
        frappe.db.commit()
        la = frappe.get_doc("Leave Application", la_name)

        ld = self._create_leave_declaration(emp, la.name, start, end)
        ld.leave_type = unpaid_type
        with self.assertRaises(frappe.exceptions.ValidationError):
            ld.insert()
