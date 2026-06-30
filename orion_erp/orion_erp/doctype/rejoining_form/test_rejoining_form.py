import frappe
from frappe.tests.utils import FrappeTestCase


class TestRejoiningForm(FrappeTestCase):
    def setUp(self):
        frappe.db.delete("Rejoining Form", {"name": ["like", "HR-RF-%"]})
        frappe.db.commit()

    def _create_rejoining_form(self, employee=None, leave_type=None, skip_approver_fields=False):
        if not employee:
            employee = self._get_test_employee()

        rf = frappe.get_doc({
            "doctype": "Rejoining Form",
            "naming_series": "HR-RF-.YYYY.-",
            "employee": employee,
            "leave_start_date": "2026-01-01",
            "leave_end_date": "2026-01-15",
            "leave_type": leave_type or "Annual Leave",
            "reporting_date": "2026-01-16",
            "reporting_time": "09:00:00",
            "reporting_location": "Main Office",
            "department_in_charge_id": "Administrator",
            "hr_id": "Administrator",
            "date_hr": "2026-01-16",
            "date_incharge": "2026-01-16",
            "approved_rejoining_date": "2026-01-16",
            "site_allocated": "Main Site",
            "mobilization__date": "2026-01-16",
            "tentative_rejoining_date": "2026-01-16",
            "actual_rejoining_date": "2026-01-16",
        })
        if not skip_approver_fields:
            # Establish a fresh consistent-read snapshot so fetch_from sees our
            # db_set_value writes under REPEATABLE READ isolation.
            frappe.db.sql(f"SELECT leave_approver FROM `tabEmployee` WHERE name = %s FOR UPDATE", employee)
            frappe.db.set_value("Employee", employee, "leave_approver", "Administrator")
            frappe.db.set_value("Employee", employee, "custom_leave_approver_1", "Administrator")
            rf.custom_rejoining_approver_1 = "Administrator"
            rf.custom_rejoining_approver_2 = "Administrator"
            rf.custom_status_rejoining_approver1 = "Open"
            rf.custom_status_rejoining_approver2 = "Open"
        rf.insert(ignore_permissions=True)
        return rf

    def _get_test_employee(self):
        emp = frappe.db.get_value("Employee", {}, "name", order_by="creation")
        if not emp:
            emp = frappe.get_doc({
                "doctype": "Employee",
                "first_name": "Test",
                "last_name": "Employee",
                "company": frappe.defaults.get_defaults().get("company") or "_Test Company",
                "date_of_joining": "2020-01-01",
            }).insert(ignore_permissions=True).name
        return emp

    def test_create_rejoining_form(self):
        rf = self._create_rejoining_form()
        self.assertTrue(rf.name)
        self.assertEqual(rf.docstatus, 0)

    def test_validate_approval_flow(self):
        employee = self._get_test_employee()
        # Clear the employee's leave_approver. Use SELECT...FOR UPDATE to
        # establish a new consistent-read snapshot so fetch_from (a regular
        # SELECT) sees the updated value under REPEATABLE READ isolation.
        frappe.db.sql(f"SELECT leave_approver FROM `tabEmployee` WHERE name = %s FOR UPDATE", employee)
        frappe.db.set_value("Employee", employee, "leave_approver", None)
        frappe.db.set_value("Employee", employee, "custom_leave_approver_1", None)
        rf = self._create_rejoining_form(employee=employee, skip_approver_fields=True)
        # No approvers configured → status should stay Open
        self.assertIsNone(rf.custom_rejoining_approver_1, "Approver 1 should be empty")
        self.assertEqual(rf.custom_rejoining_approval_status, "Open")

    def test_approver_can_approve(self):
        rf = self._create_rejoining_form()
        rf.custom_status_rejoining_approver1 = "Approved"
        rf.save(ignore_permissions=True)
        rf.reload()
        # Only approver 1 approved, approver 2 still pending
        self.assertEqual(rf.custom_rejoining_approval_status, "Pending Approval from Approver 2")

    def test_approver_full_flow(self):
        rf = self._create_rejoining_form()
        rf.custom_status_rejoining_approver1 = "Approved"
        rf.custom_status_rejoining_approver2 = "Approved"
        rf.save(ignore_permissions=True)
        rf.reload()
        self.assertEqual(rf.docstatus, 1)
        self.assertEqual(rf.custom_rejoining_approval_status, "Approved")

    def test_reject_rejoining_form(self):
        rf = self._create_rejoining_form()
        rf.custom_status_rejoining_approver1 = "Rejected"
        rf.save(ignore_permissions=True)
        rf.reload()
        self.assertEqual(rf.custom_rejoining_approval_status, "Rejected")

    def test_cancel_draft(self):
        rf = self._create_rejoining_form()
        from orion_erp.orion_erp.validations.rejoining_form import cancel_draft_rejoining
        result = cancel_draft_rejoining(rf.name)
        self.assertTrue(result)
        frappe.db.commit()
        rf.reload()
        self.assertEqual(rf.docstatus, 2)
        self.assertEqual(rf.custom_rejoining_approval_status, "Cancelled")

    def test_reset_on_amend(self):
        rf = self._create_rejoining_form()
        rf.custom_status_rejoining_approver1 = "Approved"
        rf.custom_status_rejoining_approver2 = "Approved"
        rf.save(ignore_permissions=True)
        rf.reload()
        self.assertEqual(rf.docstatus, 1, "Form should be submitted before amend test")
        cancel_doc = frappe.get_doc("Rejoining Form", rf.name)
        cancel_doc.cancel()
        amend = frappe.copy_doc(cancel_doc)
        amend.amended_from = cancel_doc.name
        amend.docstatus = 0
        amend.insert(ignore_permissions=True)
        self.assertEqual(amend.custom_status_rejoining_approver1, "Open")
