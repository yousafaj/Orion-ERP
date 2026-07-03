__version__ = "0.0.1"

# Monkey patch
from frappe.core.doctype.file.file import File
from orion_erp.orion_erp.override.files import is_remote_file,get_full_path
File.is_remote_file = property(is_remote_file)
File.get_full_path = get_full_path

# Patch get_number_of_leave_days to include sandwich leave days
import hrms.hr.doctype.leave_application.leave_application as _la_module
from orion_erp.orion_erp.validations.leave_application import (
    patched_get_number_of_leave_days,
    patched_update_attendance,
    patched_cancel_attendance,
    _save_original_get_number_of_leave_days,
    _save_original_update_attendance,
    _save_original_cancel_attendance,
    _original_get_number_of_leave_days,
    _original_update_attendance,
    _original_cancel_attendance,
)
_save_original_get_number_of_leave_days(_la_module.get_number_of_leave_days)
_la_module.get_number_of_leave_days = patched_get_number_of_leave_days

_save_original_update_attendance(_la_module.LeaveApplication.update_attendance)
_la_module.LeaveApplication.update_attendance = patched_update_attendance

_save_original_cancel_attendance(_la_module.LeaveApplication.cancel_attendance)
_la_module.LeaveApplication.cancel_attendance = patched_cancel_attendance

# Suppress the HRMS notification on draft save — Orion handles approval emails
def _noop_notify_leave_approver(self):
    pass

_la_module.LeaveApplication.notify_leave_approver = _noop_notify_leave_approver

# Patch S3 plugin's _assert_write_permission to handle
# unsaved documents (temporary names like "new-leave-application-xxx")
import frappe_s3_attachment.controller as _s3_ctrl
import frappe

_original_assert_write_permission = _s3_ctrl._assert_write_permission

def _patched_assert_write_permission(doctype, docname, **kwargs):
    if not doctype or doctype == "File" or not docname:
        return
    try:
        has_perm = frappe.has_permission(doctype, "write", docname)
    except frappe.DoesNotExistError:
        return
    if not has_perm:
        frappe.throw(
            frappe._("You do not have permission to attach files to {0} {1}.").format(
                doctype, docname
            ),
            frappe.PermissionError,
        )

_s3_ctrl._assert_write_permission = _patched_assert_write_permission
