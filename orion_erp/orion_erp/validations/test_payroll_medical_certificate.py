import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch
import time


class _MockDoc:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def set(self, fieldname, value):
        setattr(self, fieldname, value)

    def append(self, fieldname, value):
        getattr(self, fieldname).append(value)


_LEAVE_TYPE_NAME = "_Test Sick Leave MC Required"
_HR_EMAIL = "test_hr_mc@example.com"
_EMPLOYEE_USER = "test_emp_mc_req@example.com"
_TS = str(int(time.time() * 1000))
_la_counter = 0


def _ensure_leave_type():
    if frappe.db.exists("Leave Type", _LEAVE_TYPE_NAME):
        frappe.db.set_value("Leave Type", _LEAVE_TYPE_NAME, "custom_medical_certificate_required", 1)
        return frappe.get_doc("Leave Type", _LEAVE_TYPE_NAME)
    doc = frappe.get_doc({
        "doctype": "Leave Type",
        "leave_type_name": _LEAVE_TYPE_NAME,
        "custom_medical_certificate_required": 1,
    })
    doc.flags.ignore_permissions = True
    doc.insert()
    return doc


def _ensure_hr_user():
    if not frappe.db.exists("User", _HR_EMAIL):
        user = frappe.get_doc({
            "doctype": "User",
            "email": _HR_EMAIL,
            "first_name": "Test HR MC",
            "new_password": "test123",
            "roles": [{"role": "HR Manager"}],
        })
        user.flags.ignore_permissions = True
        user.insert()
        frappe.db.commit()
    frappe.db.set_value("User", _HR_EMAIL, "enabled", 1)
    if not frappe.db.exists("Has Role", {"parent": _HR_EMAIL, "role": "HR Manager"}):
        frappe.get_doc({
            "doctype": "Has Role",
            "parent": _HR_EMAIL,
            "parenttype": "User",
            "parentfield": "roles",
            "role": "HR Manager",
        }).insert(ignore_permissions=True)
    return frappe.get_doc("User", _HR_EMAIL)


def _ensure_employee_user():
    if frappe.db.exists("User", _EMPLOYEE_USER):
        return frappe.get_doc("User", _EMPLOYEE_USER)
    user = frappe.get_doc({
        "doctype": "User",
        "email": _EMPLOYEE_USER,
        "first_name": "Test Emp MC User",
        "new_password": "test123",
        "roles": [{"role": "Employee"}],
    })
    user.flags.ignore_permissions = True
    user.insert()
    frappe.db.commit()
    return user


def _get_existing_company():
    result = frappe.db.sql(
        "SELECT name FROM `tabCompany` WHERE docstatus < 2 LIMIT 1",
        as_dict=True,
    )
    if result:
        return result[0].name
    raise ValueError("No company found on the test site")


def _cleanup_stale_test_data():
    frappe.db.sql("DELETE FROM `tabLeave Application` WHERE name LIKE 'TEST-LA-MC-%'")
    frappe.db.sql("DELETE FROM `tabEmployee` WHERE name LIKE 'TEST-EMP-MC-%'")
    frappe.db.sql(
        "UPDATE `tabEmployee` SET user_id=NULL WHERE user_id=%s AND name NOT LIKE 'TEST-EMP-MC-%%'",
        (_EMPLOYEE_USER,),
    )
    frappe.db.commit()


def _create_test_employee(company):
    _ensure_employee_user()
    emp_id = f"TEST-EMP-MC-{_TS}"
    existing = frappe.db.get_value("Employee", emp_id, "user_id")
    if existing:
        if existing == _EMPLOYEE_USER:
            return emp_id
        frappe.db.set_value("Employee", emp_id, "user_id", _EMPLOYEE_USER)
        return emp_id
    from orion_erp.orion_erp.validations.employee_hooks import validate_employee
    with patch("orion_erp.orion_erp.validations.employee_hooks.validate_employee"):
        emp = frappe.get_doc({
            "doctype": "Employee",
            "employee": emp_id,
            "employee_name": "Test Emp MC",
            "first_name": "Test Emp MC",
            "company": company,
            "user_id": _EMPLOYEE_USER,
            "date_of_joining": "2020-01-01",
            "date_of_birth": "1990-01-01",
            "status": "Active",
            "gender": "Male",
            "custom_total_salary_as_per_offer_letter": 0,
        })
        emp.flags.ignore_permissions = True
        emp.insert()
    frappe.db.set_value("Employee", emp.name, "user_id", _EMPLOYEE_USER)
    return emp.name


def _create_leave_application(employee, employee_name, leave_type,
                               from_date, to_date, company,
                               medical_certificate=None):
    """Create a submitted Leave Application via raw SQL, bypassing all hooks."""
    global _la_counter
    _la_counter += 1
    name = f"TEST-LA-MC-{_TS}-{_la_counter}"
    mc_value = medical_certificate or ""
    mc_status = "Submitted" if medical_certificate else "Pending"

    frappe.db.sql("""
        INSERT INTO `tabLeave Application` (
            name, creation, modified, modified_by, owner,
            docstatus, idx, employee, employee_name, leave_type,
            company, from_date, to_date, half_day, total_leave_days,
            leave_approver, posting_date, status,
            follow_via_email, custom_status_approver1,
            custom_status_approver2, custom_status_approver4,
            custom_status_approver5, custom_medical_certificate,
            custom_medical_certificate_status, custom_reminder_sent,
            custom_escalation_sent, custom_sent_for_approval,
            custom_leave_balance_after
        ) VALUES (
            %s, NOW(), NOW(), 'Administrator', 'Administrator',
            1, 0, %s, %s, %s,
            %s, %s, %s, 0, 0.0,
            'Administrator', %s, 'Approved',
            1, 'Open',
            'Open', 'Open',
            'Open', %s,
            %s, 0,
            0, 0,
            0.0
        )
    """, (
        name, employee, employee_name, leave_type,
        company, from_date, to_date, frappe.utils.today(),
        mc_value, mc_status,
    ), as_dict=True)

    return name


class TestPayrollMedicalCertificate(FrappeTestCase):

    def setUp(self):
        _cleanup_stale_test_data()
        self.company = _get_existing_company()
        self.leave_type = _ensure_leave_type()
        self.hr_user = _ensure_hr_user()
        self.today = frappe.utils.today()
        self.start_date = frappe.utils.add_days(self.today, -15)
        self.end_date = frappe.utils.add_days(self.today, 15)
        self.employee = _create_test_employee(self.company)
        self.employee_name = "Test Emp MC"

    def tearDown(self):
        frappe.db.rollback()

    # ------------------------------------------------------------------
    # _get_employees_with_pending_medical_certificates
    # ------------------------------------------------------------------
    def test_no_employees_returns_empty(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_employees_with_pending_medical_certificates,
        )
        result = _get_employees_with_pending_medical_certificates(
            self.company, self.start_date, self.end_date, []
        )
        self.assertEqual(result, [])

    def test_no_leave_types_requiring_mc_returns_empty(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_employees_with_pending_medical_certificates,
        )
        frappe.db.sql(
            "UPDATE `tabLeave Type` SET custom_medical_certificate_required=0"
        )
        result = _get_employees_with_pending_medical_certificates(
            self.company, self.start_date, self.end_date,
            [self.employee],
        )
        self.assertEqual(result, [])

    def test_no_matching_leave_apps_returns_empty(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_employees_with_pending_medical_certificates,
        )
        result = _get_employees_with_pending_medical_certificates(
            self.company, self.start_date, self.end_date,
            [self.employee],
        )
        self.assertEqual(result, [])

    def test_leave_app_without_mc_is_found(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_employees_with_pending_medical_certificates,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        result = _get_employees_with_pending_medical_certificates(
            self.company, self.start_date, self.end_date,
            [self.employee],
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].employee, self.employee)

    def test_leave_app_with_mc_not_in_result(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_employees_with_pending_medical_certificates,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="/files/medical_cert.pdf",
        )
        result = _get_employees_with_pending_medical_certificates(
            self.company, self.start_date, self.end_date,
            [self.employee],
        )
        self.assertEqual(result, [])

    def test_empty_string_mc_treated_as_pending(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_employees_with_pending_medical_certificates,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        result = _get_employees_with_pending_medical_certificates(
            self.company, self.start_date, self.end_date,
            [self.employee],
        )
        self.assertTrue(len(result) >= 1)

    def test_deduplicates_by_leave_application_name(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_employees_with_pending_medical_certificates,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        result = _get_employees_with_pending_medical_certificates(
            self.company, self.start_date, self.end_date,
            [self.employee],
        )
        names = [r.name for r in result]
        self.assertEqual(len(names), len(set(names)))

    # ------------------------------------------------------------------
    # validate_medical_certificate_for_payroll_entry
    # ------------------------------------------------------------------
    def test_payroll_entry_no_pending_mc_no_changes(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_payroll_entry,
        )
        doc = _MockDoc(
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employees=[_MockDoc(employee=self.employee, employee_name=self.employee_name)],
        )
        with patch("frappe.msgprint") as mock_msg:
            validate_medical_certificate_for_payroll_entry(doc)
            mock_msg.assert_not_called()
        self.assertEqual(len(doc.employees), 1)

    def test_payroll_entry_pending_mc_employees_removed(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_payroll_entry,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        doc = _MockDoc(
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employees=[_MockDoc(employee=self.employee, employee_name=self.employee_name)],
        )
        with patch("frappe.sendmail"), patch("frappe.msgprint"):
            validate_medical_certificate_for_payroll_entry(doc)
        self.assertEqual(len(doc.employees), 0)

    def test_payroll_entry_all_employees_pending(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_payroll_entry,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        doc = _MockDoc(
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employees=[_MockDoc(employee=self.employee, employee_name=self.employee_name)],
        )
        with patch("frappe.sendmail"), patch("frappe.msgprint"):
            validate_medical_certificate_for_payroll_entry(doc)
        self.assertEqual(len(doc.employees), 0)

    def test_payroll_entry_employee_email_sent(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_payroll_entry,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        doc = _MockDoc(
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employees=[_MockDoc(employee=self.employee, employee_name=self.employee_name)],
        )
        with patch("frappe.sendmail") as mock_send, patch("frappe.msgprint"):
            validate_medical_certificate_for_payroll_entry(doc)
            employee_emails = [
                c for c in mock_send.call_args_list
                if _EMPLOYEE_USER in str(c.kwargs.get("recipients", []))
                and "Medical Certificate" in c.kwargs.get("subject", "")
            ]
            self.assertTrue(len(employee_emails) > 0,
                            f"Expected employee reminder email but got: {mock_send.call_args_list}")

    def test_payroll_entry_hr_email_sent(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_payroll_entry,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        doc = _MockDoc(
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employees=[_MockDoc(employee=self.employee, employee_name=self.employee_name)],
        )
        with patch("frappe.sendmail") as mock_send, patch("frappe.msgprint"):
            validate_medical_certificate_for_payroll_entry(doc)
            hr_emails = [
                c for c in mock_send.call_args_list
                if _HR_EMAIL in str(c.kwargs.get("recipients", []))
                and "Payroll" in c.kwargs.get("subject", "")
            ]
            self.assertTrue(len(hr_emails) > 0,
                            f"Expected HR notification but got: {mock_send.call_args_list}")

    def test_payroll_entry_msgprint_shows_skipped(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_payroll_entry,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        doc = _MockDoc(
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employees=[_MockDoc(employee=self.employee, employee_name=self.employee_name)],
        )
        with patch("frappe.sendmail"), patch("frappe.msgprint") as mock_msg:
            validate_medical_certificate_for_payroll_entry(doc)
            mock_msg.assert_called_once()
            msg_str = str(mock_msg.call_args)
            self.assertIn(self.employee_name, msg_str)

    # ------------------------------------------------------------------
    # validate_medical_certificate_for_salary_slip
    # ------------------------------------------------------------------
    def test_salary_slip_draft_throws_when_mc_pending(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_salary_slip,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        doc = _MockDoc(
            docstatus=0,
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employee=self.employee,
            employee_name=self.employee_name,
        )
        with patch("frappe.sendmail"):
            with self.assertRaises(frappe.exceptions.ValidationError):
                validate_medical_certificate_for_salary_slip(doc)

    def test_salary_slip_submitted_skips_validation(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_salary_slip,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        doc = _MockDoc(
            docstatus=1,
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employee=self.employee,
            employee_name=self.employee_name,
        )
        with patch("frappe.sendmail") as mock_send:
            validate_medical_certificate_for_salary_slip(doc)
            mock_send.assert_not_called()

    def test_salary_slip_draft_no_pending_mc_passes(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_salary_slip,
        )
        doc = _MockDoc(
            docstatus=0,
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employee=self.employee,
            employee_name=self.employee_name,
        )
        with patch("frappe.sendmail") as mock_send:
            validate_medical_certificate_for_salary_slip(doc)
            mock_send.assert_not_called()

    def test_salary_slip_employee_email_sent(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_salary_slip,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        doc = _MockDoc(
            docstatus=0,
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employee=self.employee,
            employee_name=self.employee_name,
        )
        with patch("frappe.sendmail") as mock_send:
            with self.assertRaises(frappe.exceptions.ValidationError):
                validate_medical_certificate_for_salary_slip(doc)
            employee_emails = [
                c for c in mock_send.call_args_list
                if _EMPLOYEE_USER in str(c.kwargs.get("recipients", []))
                and "Medical Certificate" in c.kwargs.get("subject", "")
            ]
            self.assertTrue(len(employee_emails) > 0,
                            f"Expected employee email but got: {mock_send.call_args_list}")

    def test_salary_slip_hr_email_sent(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            validate_medical_certificate_for_salary_slip,
        )
        _create_leave_application(
            employee=self.employee,
            employee_name=self.employee_name,
            leave_type=self.leave_type.name,
            from_date=self.start_date,
            to_date=self.end_date,
            company=self.company,
            medical_certificate="",
        )
        doc = _MockDoc(
            docstatus=0,
            company=self.company,
            start_date=self.start_date,
            end_date=self.end_date,
            employee=self.employee,
            employee_name=self.employee_name,
        )
        with patch("frappe.sendmail") as mock_send:
            with self.assertRaises(frappe.exceptions.ValidationError):
                validate_medical_certificate_for_salary_slip(doc)
            hr_emails = [
                c for c in mock_send.call_args_list
                if _HR_EMAIL in str(c.kwargs.get("recipients", []))
                and "Payroll" in c.kwargs.get("subject", "")
            ]
            self.assertTrue(len(hr_emails) > 0,
                            f"Expected HR email but got: {mock_send.call_args_list}")

    # ------------------------------------------------------------------
    # _get_hr_user_emails
    # ------------------------------------------------------------------
    def test_get_hr_emails_configured_roles(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_hr_user_emails,
        )
        settings = frappe.get_single("Orion Settings")
        settings.excess_leave_notification_roles = []
        settings.append("excess_leave_notification_roles", {"role": "HR Manager"})
        settings.save()
        frappe.db.commit()

        emails = _get_hr_user_emails()
        self.assertIn(_HR_EMAIL, emails,
                      f"HR user should be in result, got: {emails}")

    def test_get_hr_emails_fallback(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_hr_user_emails,
        )
        settings = frappe.get_single("Orion Settings")
        settings.excess_leave_notification_roles = []
        settings.save()
        frappe.db.commit()

        emails = _get_hr_user_emails()
        self.assertIsInstance(emails, list)

    def test_get_hr_emails_disabled_users_excluded(self):
        from orion_erp.orion_erp.validations.payroll_medical_certificate import (
            _get_hr_user_emails,
        )
        settings = frappe.get_single("Orion Settings")
        settings.excess_leave_notification_roles = []
        settings.append("excess_leave_notification_roles", {"role": "HR Manager"})
        settings.save()
        frappe.db.commit()

        frappe.db.set_value("User", self.hr_user.name, "enabled", 0)
        frappe.db.commit()

        emails = _get_hr_user_emails()
        self.assertNotIn(_HR_EMAIL, emails,
                         "Disabled user should not appear in HR email list")
