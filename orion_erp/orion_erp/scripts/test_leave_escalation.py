import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
from unittest.mock import patch, MagicMock
import datetime
import time


class TestLeaveEscalation(FrappeTestCase):
    def setUp(self):
        self.setup_escalation_config()
        self.find_existing_employee()

    def tearDown(self):
        frappe.db.rollback()

    def setup_escalation_config(self):
        self.hr_manager = "test_hr_manager_esc3@example.com"
        self.approver1 = "test_approver1_esc3@example.com"
        self.approver2 = "test_approver2_esc3@example.com"
        for email, first_name, roles in [
            (self.hr_manager, "Test HR Manager Esc", ["HR Manager"]),
            (self.approver1, "Test Approver 1 Esc", ["Leave Approver"]),
            (self.approver2, "Test Approver 2 Esc", ["Leave Approver"]),
        ]:
            if not frappe.db.exists("User", email):
                user = frappe.get_doc({
                    "doctype": "User",
                    "email": email,
                    "first_name": first_name,
                    "new_password": "test123",
                    "roles": [{"role": r} for r in roles]
                })
                user.insert(ignore_permissions=True)

        lt_result = frappe.db.sql(
            "SELECT name FROM `tabLeave Type` WHERE name LIKE '%annual%' LIMIT 1",
            as_dict=True
        )
        self.leave_type = lt_result[0].name if lt_result else "Annual Leave"

        settings = frappe.get_single("Orion Settings")
        settings.default_escalation_user = self.hr_manager
        settings.leave_escalation_rules = []
        settings.append("leave_escalation_rules", {
            "leave_type": self.leave_type,
            "enabled": 1,
            "reminder_minutes": 1,
            "escalation_minutes": 2
        })
        settings.save()
        frappe.db.commit()

    def find_existing_employee(self):
        emp = frappe.db.sql(
            "SELECT name, employee_name FROM `tabEmployee` WHERE status='Active' LIMIT 1",
            as_dict=True
        )
        self.employee_name = emp[0].name if emp else None
        self.employee_name_val = emp[0].employee_name if emp else "Test"

    def _minutes_ago(self, minutes):
        return now_datetime() - datetime.timedelta(minutes=minutes)

    def _minutes_from_now(self, minutes):
        return now_datetime() + datetime.timedelta(minutes=minutes)

    def create_test_leave_application(self):
        if not self.employee_name:
            self.skipTest("No active employee found in database")

        leave_name = "TEST-ESC-" + str(int(time.time() * 1000))
        now = now_datetime()

        frappe.db.sql(
            "INSERT INTO `tabLeave Application`"
            "(`name`, `employee`, `employee_name`, `leave_type`, `from_date`, `to_date`,"
            " `status`, `docstatus`, `leave_approver`, `custom_leave_approver_1`,"
            " `custom_leave_approver_4`, `custom_leave_approver_5`,"
            " `custom_approval_status`, `custom_last_status_change`, `custom_reminder_sent`,"
            " `custom_escalation_sent`,"
            " `creation`, `modified`)"
            " VALUES"
            "(%s, %s, %s, %s, %s, %s,"
            " %s, 0, %s, %s,"
            " %s, %s,"
            " %s, %s, 0, 0,"
            " %s, %s)",
            (
                leave_name,
                self.employee_name,
                self.employee_name_val,
                self.leave_type,
                self._minutes_from_now(24),
                self._minutes_from_now(48),
                "Open",
                self.approver1,
                self.approver2,
                "",
                "",
                "Pending Approval from Approver 1",
                now,
                now,
                now,
            ),
        )
        frappe.db.commit()
        return leave_name

    def _get_la_dict(self, leave_name):
        fields = [
            "name", "employee_name", "leave_type", "leave_approver",
            "custom_leave_approver_1", "custom_leave_approver_2",
            "custom_leave_approver_4", "custom_leave_approver_5",
            "status", "custom_status_approver1", "custom_status_approver2",
            "custom_status_approver4", "custom_status_approver5",
            "custom_last_status_change", "custom_reminder_sent",
            "custom_escalation_sent",
            "custom_approval_status", "creation"
        ]
        data = frappe.db.get_value("Leave Application", leave_name, fields, as_dict=True)
        return frappe._dict(data)

    def test_01_escalation_rules_configuration(self):
        from orion_erp.orion_erp.scripts.leave_escalation import _build_escalation_rules_map
        settings = frappe.get_single("Orion Settings")
        rules = _build_escalation_rules_map(settings)
        self.assertIn(self.leave_type, rules)
        self.assertEqual(rules[self.leave_type]["reminder_minutes"], 1)
        self.assertEqual(rules[self.leave_type]["escalation_minutes"], 2)
        print("PASS: test_01_escalation_rules_configuration")

    def test_02_get_minutes_waiting(self):
        from orion_erp.orion_erp.scripts.leave_escalation import _get_minutes_waiting
        leave_name = self.create_test_leave_application()
        la = self._get_la_dict(leave_name)
        minutes = _get_minutes_waiting(la)
        self.assertIsNotNone(minutes)
        self.assertGreaterEqual(minutes, 0)
        print("PASS: test_02_get_minutes_waiting")

    def test_03_get_pending_level(self):
        from orion_erp.orion_erp.scripts.leave_escalation import _get_pending_level
        leave_name = self.create_test_leave_application()
        la = self._get_la_dict(leave_name)
        pending = _get_pending_level(la)
        self.assertIsNotNone(pending)
        self.assertEqual(pending["approver_field"], "leave_approver")
        print("PASS: test_03_get_pending_level")

    def test_04_reminder_email(self):
        from orion_erp.orion_erp.scripts.leave_escalation import _send_reminder
        leave_name = self.create_test_leave_application()
        frappe.db.set_value("Leave Application", leave_name,
            "custom_last_status_change", self._minutes_ago(1.5))
        frappe.db.commit()
        with patch("frappe.sendmail") as mock_sendmail:
            _send_reminder(leave_name, self.approver1, "leave_approver", self.leave_type)
            mock_sendmail.assert_called_once()
            call_args = mock_sendmail.call_args
            self.assertIn(self.approver1, call_args.kwargs.get("recipients", []))
            self.assertIn("Reminder", call_args.kwargs.get("subject", ""))
            reminder_sent = frappe.db.get_value("Leave Application", leave_name, "custom_reminder_sent")
            self.assertEqual(reminder_sent, 1)
        print("PASS: test_04_reminder_email")

    def test_05_escalation_to_hr(self):
        from orion_erp.orion_erp.scripts.leave_escalation import _escalate
        leave_name = self.create_test_leave_application()
        with patch("frappe.sendmail") as mock_sendmail, \
             patch("frappe.get_doc") as mock_get_doc:
            mock_doc = MagicMock()
            mock_get_doc.return_value = mock_doc
            _escalate(leave_name, "leave_approver", self.approver1,
                      self.hr_manager, self.leave_type)
            approver_after = frappe.db.get_value("Leave Application", leave_name, "leave_approver")
            self.assertEqual(approver_after, self.approver1,
                "Escalation should NOT change the approver")
            last_change = frappe.db.get_value("Leave Application", leave_name, "custom_last_status_change")
            self.assertIsNotNone(last_change)
            escalation_sent = frappe.db.get_value("Leave Application", leave_name, "custom_escalation_sent")
            self.assertEqual(escalation_sent, 1,
                "Escalation should mark custom_escalation_sent=1")
            self.assertEqual(mock_sendmail.call_count, 1,
                "Only HR Manager should be notified, not the approver")
        print("PASS: test_05_escalation_to_hr")

    def test_06_timer_reset(self):
        leave_name = self.create_test_leave_application()
        past_time = self._minutes_ago(5)
        frappe.db.set_value("Leave Application", leave_name, "custom_last_status_change", past_time)
        frappe.db.commit()

        frappe.db.set_value("Leave Application", leave_name, "status", "Approved")
        frappe.db.set_value("Leave Application", leave_name, "custom_last_status_change", now_datetime())
        frappe.db.set_value("Leave Application", leave_name, "custom_reminder_sent", 0)
        frappe.db.commit()

        new_time = frappe.db.get_value("Leave Application", leave_name, "custom_last_status_change")
        self.assertNotEqual(str(new_time), str(past_time))
        reminder_sent = frappe.db.get_value("Leave Application", leave_name, "custom_reminder_sent")
        self.assertEqual(reminder_sent, 0)
        print("PASS: test_06_timer_reset")

    def test_07_escalation_notifies_hr_manager(self):
        from orion_erp.orion_erp.scripts.leave_escalation import _process_single_leave, _build_escalation_rules_map
        leave_name = self.create_test_leave_application()
        frappe.db.set_value("Leave Application", leave_name, "custom_last_status_change", self._minutes_ago(3))
        frappe.db.commit()
        settings = frappe.get_single("Orion Settings")
        escalation_rules = _build_escalation_rules_map(settings)
        la = self._get_la_dict(leave_name)

        with patch("orion_erp.orion_erp.scripts.leave_escalation._escalate") as mock_escalate, \
             patch("orion_erp.orion_erp.scripts.leave_escalation._send_reminder") as mock_reminder:
            _process_single_leave(la, escalation_rules, self.hr_manager)
            mock_escalate.assert_called_once()
            mock_reminder.assert_not_called()
        print("PASS: test_07_escalation_notifies_hr_manager")

    def test_08_full_flow(self):
        from orion_erp.orion_erp.scripts.leave_escalation import process_leave_escalations
        leave_name = self.create_test_leave_application()
        frappe.db.set_value("Leave Application", leave_name,
            "custom_last_status_change", self._minutes_ago(1.5))
        frappe.db.commit()
        with patch("frappe.sendmail") as mock_sendmail:
            process_leave_escalations()
            reminder_emails = [
                c for c in mock_sendmail.call_args_list
                if leave_name in str(c) and "Reminder" in str(c.kwargs.get("subject", ""))
            ]
            self.assertTrue(len(reminder_emails) > 0,
                f"Expected reminder email for {leave_name} but got: {mock_sendmail.call_args_list}")
        print("PASS: test_08_full_flow")

    def test_09_disabled_rule(self):
        from orion_erp.orion_erp.scripts.leave_escalation import _build_escalation_rules_map
        settings = frappe.get_single("Orion Settings")
        for rule in settings.leave_escalation_rules:
            rule.enabled = 0
        settings.save()
        frappe.db.commit()
        rules = _build_escalation_rules_map(settings)
        self.assertNotIn(self.leave_type, rules)
        print("PASS: test_09_disabled_rule")

    def test_10_no_escalation_user(self):
        from orion_erp.orion_erp.scripts.leave_escalation import _process_single_leave, _build_escalation_rules_map
        leave_name = self.create_test_leave_application()
        settings = frappe.get_single("Orion Settings")
        settings.default_escalation_user = ""
        settings.save()
        frappe.db.commit()
        escalation_rules = _build_escalation_rules_map(settings)
        la = self._get_la_dict(leave_name)
        _process_single_leave(la, escalation_rules, "")
        print("PASS: test_10_no_escalation_user")

    def test_11_escalation_fires_once(self):
        from orion_erp.orion_erp.scripts.leave_escalation import _process_single_leave, _build_escalation_rules_map
        leave_name = self.create_test_leave_application()
        frappe.db.set_value("Leave Application", leave_name, "custom_last_status_change", self._minutes_ago(3))
        frappe.db.commit()
        settings = frappe.get_single("Orion Settings")
        escalation_rules = _build_escalation_rules_map(settings)

        la = self._get_la_dict(leave_name)
        with patch("orion_erp.orion_erp.scripts.leave_escalation._escalate") as mock_escalate:
            _process_single_leave(la, escalation_rules, self.hr_manager)
            self.assertEqual(mock_escalate.call_count, 1, "Escalation should fire once")

        frappe.db.set_value("Leave Application", leave_name, "custom_escalation_sent", 1)
        frappe.db.commit()

        la2 = self._get_la_dict(leave_name)
        with patch("orion_erp.orion_erp.scripts.leave_escalation._escalate") as mock_escalate2:
            _process_single_leave(la2, escalation_rules, self.hr_manager)
            mock_escalate2.assert_not_called()
        print("PASS: test_11_escalation_fires_once")

    def test_12_flags_reset_on_status_change(self):
        from orion_erp.orion_erp.validations.leave_application import handle_leave_approval
        leave_name = self.create_test_leave_application()

        frappe.db.set_value("Leave Application", leave_name, "custom_reminder_sent", 1)
        frappe.db.set_value("Leave Application", leave_name, "custom_escalation_sent", 1)
        frappe.db.commit()

        old_doc = frappe.get_doc("Leave Application", leave_name)
        frappe.db.set_value("Leave Application", leave_name, "status", "Approved")
        frappe.db.commit()
        new_doc = frappe.get_doc("Leave Application", leave_name)

        new_doc._doc_before_save = old_doc
        handle_leave_approval(new_doc)

        reminder = frappe.db.get_value("Leave Application", leave_name, "custom_reminder_sent")
        escalation = frappe.db.get_value("Leave Application", leave_name, "custom_escalation_sent")
        self.assertEqual(reminder, 0, "custom_reminder_sent should reset to 0 on status change")
        self.assertEqual(escalation, 0, "custom_escalation_sent should reset to 0 on status change")
        print("PASS: test_12_flags_reset_on_status_change")
