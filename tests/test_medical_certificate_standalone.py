"""Late certificate updates must preserve approved leave and enforce file scope."""

import sys
import json
from pathlib import Path
import types
import unittest
from unittest.mock import Mock, patch

from test_leave_projection_standalone import Row, Rejected, load, throw


class CertificateTests(unittest.TestCase):
    def setUp(self):
        self.doc = Row(name="LA", leave_type="SICK", docstatus=1,
                       custom_medical_certificate="", status="Approved",
                       workflow_state="Approved", total_leave_days=3,
                       check_permission=Mock(), notify_update=Mock(), add_comment=Mock())
        self.file = Row(name="FILE", attached_to_doctype="Leave Application",
                        attached_to_name="LA", attached_to_field="custom_medical_certificate",
                        file_url="/private/files/certificate.pdf", check_permission=Mock(), save=Mock())
        self.required = True
        self.duplicate = False
        self.updates = []
        self.frappe = types.ModuleType("frappe")
        self.frappe._ = lambda text: text
        self.frappe.whitelist = lambda: lambda fn: fn
        self.frappe.throw = throw
        self.frappe.db = Row(get_value=lambda *args, **kwargs: self.required,
                            exists=lambda dt, *args: True if dt == "Leave Application" else self.duplicate,
                            set_value=lambda *args, **kwargs: self.updates.append((args, kwargs)))
        self.frappe.get_doc = lambda dt, name: self.doc if dt == "Leave Application" else self.file
        self.modules = patch.dict(sys.modules, {"frappe": self.frappe})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.module = load("medical", "orion_erp/orion_erp/services/medical_certificate.py")

    def attach(self):
        self.module.update_medical_certificate_status_on_file_attach(self.file)

    def test_late_upload_updates_submitted_application_only_certificate_fields(self):
        self.attach()
        args, kwargs = self.updates[0]
        self.assertEqual(args[2], {"custom_medical_certificate": self.file.file_url,
                                 "custom_medical_certificate_status": "Submitted"})
        self.assertFalse(kwargs["update_modified"])
        self.assertEqual(self.doc.workflow_state, "Approved")
        self.assertEqual(self.doc.total_leave_days, 3)

    def test_general_attachment_does_not_automatically_count_as_certificate(self):
        self.file.attached_to_field = None
        self.attach()
        self.assertEqual(self.updates, [])

    def test_replacement_url_updates_already_submitted_certificate(self):
        self.doc.custom_medical_certificate_status = "Submitted"
        self.doc.custom_medical_certificate = "/private/files/old.pdf"
        self.attach()
        self.assertEqual(self.updates[0][0][2]["custom_medical_certificate"], self.file.file_url)

    def test_cancelled_application_is_not_changed(self):
        self.doc.docstatus = 2
        self.attach()
        self.assertEqual(self.updates, [])
        with self.assertRaises(Rejected):
            self.module.select_medical_certificate("LA", "FILE")

    def test_deleting_current_certificate_restores_pending(self):
        self.doc.custom_medical_certificate = self.file.file_url
        self.module.reset_medical_certificate_status_on_file_trash(self.file)
        self.assertEqual(self.updates[0][0][2], {
            "custom_medical_certificate": "", "custom_medical_certificate_status": "Pending"})

    def test_deleting_old_or_duplicate_file_preserves_current_certificate(self):
        self.doc.custom_medical_certificate = "/private/files/new.pdf"
        self.module.reset_medical_certificate_status_on_file_trash(self.file)
        self.doc.custom_medical_certificate = self.file.file_url
        self.duplicate = True
        self.module.reset_medical_certificate_status_on_file_trash(self.file)
        self.assertEqual(self.updates, [])

    def test_explicit_selection_checks_permissions_and_attachment_scope(self):
        self.file.attached_to_field = None
        result = self.module.select_medical_certificate("LA", "FILE")
        self.assertEqual(result["custom_medical_certificate_status"], "Submitted")
        self.doc.check_permission.assert_called_once_with("write")
        self.file.check_permission.assert_any_call("read")
        self.file.check_permission.assert_any_call("write")
        self.file.save.assert_called_once()

    def test_other_application_or_other_attachment_field_is_rejected(self):
        for changes in ({"attached_to_name": "OTHER"}, {"attached_to_field": "custom_child_birth_certificate"}):
            with self.subTest(changes=changes):
                original = dict(self.file)
                self.file.update(changes)
                with self.assertRaises(Rejected):
                    self.module.select_medical_certificate("LA", "FILE")
                self.file.clear()
                self.file.update(original)
        self.assertEqual(self.updates, [])

    def test_unauthorized_user_is_rejected_before_any_write(self):
        self.doc.check_permission.side_effect = Rejected("Not permitted")
        with self.assertRaises(Rejected):
            self.module.select_medical_certificate("LA", "FILE")
        self.assertEqual(self.updates, [])


class PreviewTests(unittest.TestCase):
    def setUp(self):
        from test_leave_projection_standalone import BalanceTests
        fixture = BalanceTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.frappe = fixture.frappe
        self.frappe.flags = Row(mute_messages=False)
        self.frappe.ValidationError = Rejected
        self.controller = fixture.controller

    def test_invalid_preview_returns_warning_while_strict_validation_still_fails(self):
        with patch.object(self.controller, "balance_summary", side_effect=Rejected("Annual dates invalid")):
            result = self.controller.get_projected_leave_balance("EMP", "ANNUAL", "2026-11-12", "2026-11-30", display_only=1)
            self.assertEqual(result.projection_error, "Annual dates invalid")
            self.assertFalse(self.frappe.flags.mute_messages)
            with self.assertRaises(Rejected):
                self.controller.get_projected_leave_balance("EMP", "ANNUAL", "2026-11-12", "2026-11-30")

    def test_sick_leave_uses_native_balance_without_annual_projection(self):
        with patch.object(self.controller, "balance_summary") as balance:
            self.assertIsNone(self.controller.get_projected_leave_balance("EMP", "SICK", "2026-11-12", "2026-11-30", display_only=1))
            balance.assert_not_called()

    def test_preview_restores_mute_flag_after_unexpected_error(self):
        with patch.object(self.controller, "balance_summary", side_effect=RuntimeError("DB failure")):
            with self.assertRaises(RuntimeError):
                self.controller.get_projected_leave_balance("EMP", "ANNUAL", "2026-11-12", "2026-11-30", display_only=1)
        self.assertFalse(self.frappe.flags.mute_messages)


class CertificatePackagingTests(unittest.TestCase):
    def test_customization_sync_preserves_late_certificate_updates(self):
        root = Path(__file__).resolve().parents[1]
        customization = json.loads((root / "orion_erp/orion_erp/custom/leave_application.json").read_text())
        fields = {field["fieldname"]: field for field in customization["custom_fields"]}
        for name in ("custom_medical_certificate", "custom_medical_certificate_status"):
            self.assertEqual(fields[name]["allow_on_submit"], 1)
        self.assertEqual(fields["custom_medical_certificate_status"]["read_only"], 1)


class CertificateValidationTests(unittest.TestCase):
    def setUp(self):
        from test_leave_projection_standalone import BalanceTests
        fixture = BalanceTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.frappe = fixture.frappe
        self.required = True
        self.frappe.db.get_value = lambda *args, **kwargs: Row(custom_medical_certificate_required=self.required)
        self.frappe.msgprint = Mock()
        self.module = load("certificate_eligibility", "orion_erp/orion_erp/validations/leave_application/eligibility.py")

    def test_missing_certificate_is_pending_without_popup_or_submission_block(self):
        doc = Row(leave_type="SICK", docstatus=1, custom_medical_certificate="")
        self.module.validate_medical_certificate(doc)
        self.assertEqual(doc.custom_medical_certificate_status, "Pending")
        self.frappe.msgprint.assert_not_called()

    def test_late_certificate_field_change_updates_computed_status(self):
        doc = Row(leave_type="SICK", docstatus=1, custom_medical_certificate="/private/files/cert.pdf")
        self.module.validate_medical_certificate(doc)
        self.assertEqual(doc.custom_medical_certificate_status, "Submitted")
        self.required = False
        self.module.validate_medical_certificate(doc)
        self.assertEqual(doc.custom_medical_certificate_status, "")
