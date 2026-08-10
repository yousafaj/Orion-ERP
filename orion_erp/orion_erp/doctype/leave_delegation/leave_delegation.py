import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate
from frappe.model.naming import make_autoname

from orion_erp.orion_erp.services.leave_delegation import (
    APPROVAL_FLOW,
    get_pending_workflows,
    check_overlapping_delegation,
    auto_delegate_leave_application,
    handle_auto_delegation_on_update,
    restore_delegations,
)


class LeaveDelegation(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from orion_erp.orion_erp.doctype.leave_delegation_detail.leave_delegation_detail import LeaveDelegationDetail

        amended_from: DF.Link | None
        delegate_user: DF.Link
        delegator_user: DF.Link
        is_active: DF.Check
        leave_delegation_detail: DF.Table[LeaveDelegationDetail]
        naming_series: DF.Literal[None]
        valid_from: DF.Date
        valid_to: DF.Date
    # end: auto-generated types

    def before_insert(self):
        today = getdate()
        year_start = today.year if today.month >= 4 else today.year - 1
        year_end = year_start + 1
        fy = f"{year_start}-{str(year_end)[2:]}"
        self.name = make_autoname(f"LD-{fy}-.#####")

    def validate(self):
        if self.delegator_user == self.delegate_user:
            frappe.throw(_("Delegator and Delegate cannot be the same user"))
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            frappe.throw(_("Valid From must be before Valid To"))

        if self.valid_from and self.valid_to and self.delegator_user:
            existing = frappe.db.get_value(
                "Leave Delegation",
                {
                    "delegator_user": self.delegator_user,
                    "docstatus": 1,
                    "is_active": 1,
                    "valid_from": ["<=", self.valid_to],
                    "valid_to": [">=", self.valid_from],
                    "name": ["!=", self.name],
                },
                "name"
            )
            if existing:
                frappe.throw(
                    _("An active Leave Delegation ({0}) already exists for {1} with overlapping dates ({2} to {3}). Please adjust the dates.").format(
                        existing, self.delegator_user, self.valid_from, self.valid_to
                    )
                )

    def on_submit(self):
        for row in self.leave_delegation_detail:
            if not row.delegate_user:
                frappe.throw(_("Delegate User is required for row at level {0}").format(row.level))
            if row.delegate_user == row.previous_reviewer:
                frappe.throw(_("Delegate User cannot be the same as Previous Reviewer for level {0}").format(row.level))
            if not frappe.db.exists("Leave Application", row.document_name):
                continue
            frappe.db.set_value("Leave Application", row.document_name, row.approver_field, row.delegate_user)
            leave_app = frappe.get_doc("Leave Application", row.document_name)
            leave_app.add_comment(
                "Info",
                _("Level {0} delegated from {1} to {2} via Leave Delegation {3}").format(
                    row.level, row.previous_reviewer, row.delegate_user, self.name
                )
            )
        self._notify_delegate_users()

    def on_cancel(self):
        for row in self.leave_delegation_detail:
            if not frappe.db.exists("Leave Application", row.document_name):
                continue
            current_approver = frappe.db.get_value("Leave Application", row.document_name, row.approver_field)
            if current_approver == row.delegate_user:
                frappe.db.set_value("Leave Application", row.document_name, row.approver_field, row.previous_reviewer)
                leave_app = frappe.get_doc("Leave Application", row.document_name)
                leave_app.add_comment(
                    "Info",
                    _("Level {0} restored from {1} to {2} via cancellation of Leave Delegation {3}").format(
                        row.level, row.delegate_user, row.previous_reviewer, self.name
                    )
                )

    def _notify_delegate_users(self):
        from collections import defaultdict
        delegate_groups = defaultdict(list)
        for row in self.leave_delegation_detail:
            if row.document_name and row.delegate_user:
                delegate_groups[row.delegate_user].append(row)

        for delegate_user, rows in delegate_groups.items():
            base_url = frappe.utils.get_url()
            rows_html = "".join(
                f"""<tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">
                        <a href="{base_url}/app/leave-application/{r.document_name}" target="_blank">{r.document_name}</a>
                    </td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Level {r.level}</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">{r.previous_reviewer}</td>
                </tr>"""
                for r in rows
            )
            subject = _("Leave Delegation Notification - {0}").format(self.name)
            message = f"""
            <h3>Leave Delegation Notification</h3>
            <p>Leave delegation <b>{self.name}</b> has been created from <b>{self.valid_from}</b> to <b>{self.valid_to}</b>.</p>
            <p>Delegator: <b>{self.delegator_user}</b></p>
            <p>The following leave applications have been delegated to you:</p>
            <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:600px;">
                <tr>
                    <th style="padding:8px;border:1px solid #f3f3f3;">Leave Application</th>
                    <th style="padding:8px;border:1px solid #f3f3f3;">Level</th>
                    <th style="padding:8px;border:1px solid #f3f3f3;">Previous Reviewer</th>
                </tr>
                {rows_html}
            </table>
            """
            try:
                frappe.sendmail(recipients=[delegate_user], subject=subject, message=message)
            except Exception:
                frappe.log_error(title="Leave Delegation Email Failed", message=f"Failed to send leave delegation email to {delegate_user}")
