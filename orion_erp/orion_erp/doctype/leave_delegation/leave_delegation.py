import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate
from frappe.model.naming import make_autoname
from collections import defaultdict

APPROVAL_FLOW = [
    {"approver_field": "leave_approver", "status_field": "status", "level": 1},
    {"approver_field": "custom_leave_approver_1", "status_field": "custom_status_approver1", "level": 2},
    {"approver_field": "custom_leave_approver_2", "status_field": "custom_status_approver2", "level": 3},
    {"approver_field": "custom_leave_approver_4", "status_field": "custom_status_approver4", "level": 4},
    {"approver_field": "custom_leave_approver_5", "status_field": "custom_status_approver5", "level": 5},
]


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
        series = f"LD-{fy}-.#####"
        self.name = make_autoname(series)

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

            frappe.sendmail(recipients=[delegate_user], subject=subject, message=message)


@frappe.whitelist()
def get_pending_workflows(delegator, valid_from=None, valid_to=None):
    delegator_user = frappe.db.get_value("User", delegator, "name")
    if not delegator_user:
        return []

    active_delegated = frappe.db.sql_list("""
        SELECT DISTINCT ldd.document_name
        FROM `tabLeave Delegation Detail` ldd
        JOIN `tabLeave Delegation` ld ON ld.name = ldd.parent
        WHERE ld.docstatus = 1
          AND ld.is_active = 1
          AND ld.delegator_user = %s
          AND ldd.document_name IS NOT NULL
    """, delegator_user)

    results = []

    for flow in APPROVAL_FLOW:
        approver_field = flow["approver_field"]
        status_field = flow["status_field"]
        level = flow["level"]

        filters = [
            ["docstatus", "=", 0],
            [approver_field, "=", delegator_user],
            [status_field, "=", "Open"],
        ]

        if active_delegated:
            filters.append(["name", "not in", active_delegated])

        if valid_from:
            filters.append(["from_date", ">=", valid_from])

        if valid_to:
            filters.append(["from_date", "<=", valid_to])

        leave_apps = frappe.get_all("Leave Application", filters=filters, fields=["name"])

        for la in leave_apps:
            results.append({
                "document_name": la.name,
                "level": level,
                "approver_field": approver_field,
                "previous_reviewer": delegator_user,
                "has_delegation": 1,
            })

    return results


@frappe.whitelist()
def check_overlapping_delegation(delegator_user, valid_from, valid_to, name=None):
    filters = {
        "delegator_user": delegator_user,
        "docstatus": 1,
        "is_active": 1,
        "valid_from": ["<=", valid_to],
        "valid_to": [">=", valid_from],
    }
    if name:
        filters["name"] = ["!=", name]

    existing = frappe.db.get_value("Leave Delegation", filters, "name")
    return bool(existing)


def auto_delegate_leave_application(doc, method=None):
    today = frappe.utils.today()

    if not hasattr(doc, '_auto_delegations'):
        doc._auto_delegations = []

    for flow in APPROVAL_FLOW:
        approver_field = flow["approver_field"]
        level = flow["level"]

        current_approver = doc.get(approver_field)
        if not current_approver:
            continue

        delegation_name = frappe.db.get_value(
            "Leave Delegation",
            {
                "delegator_user": current_approver,
                "docstatus": 1,
                "is_active": 1,
                "valid_from": ["<=", today],
                "valid_to": [">=", today],
            },
            "name"
        )

        if not delegation_name:
            continue

        delegation = frappe.get_doc("Leave Delegation", delegation_name)
        delegate_user = delegation.delegate_user

        if not delegate_user:
            continue

        if doc.name and frappe.db.exists("Leave Delegation Detail", {
            "parent": delegation_name,
            "document_name": doc.name,
            "level": level,
        }):
            continue

        doc._auto_delegations.append({
            "delegation_name": delegation_name,
            "delegate_user": delegate_user,
            "approver_field": approver_field,
            "level": level,
            "previous_reviewer": current_approver,
        })

        doc.set(approver_field, delegate_user)


def handle_auto_delegation_on_update(doc, method=None):
    auto_delegations = getattr(doc, '_auto_delegations', [])
    if not auto_delegations:
        return

    for info in auto_delegations:
        already = frappe.db.exists("Leave Delegation Detail", {
            "parent": info["delegation_name"],
            "document_name": doc.name,
            "level": info["level"],
        })
        if already:
            continue

        max_idx = frappe.db.sql("""
            SELECT COALESCE(MAX(idx), 0) FROM `tabLeave Delegation Detail`
            WHERE parent = %s
        """, info["delegation_name"])[0][0]

        child = frappe.new_doc("Leave Delegation Detail")
        child.parent = info["delegation_name"]
        child.parentfield = "leave_delegation_detail"
        child.parenttype = "Leave Delegation"
        child.document_name = doc.name
        child.level = info["level"]
        child.approver_field = info["approver_field"]
        child.previous_reviewer = info["previous_reviewer"]
        child.delegate_user = info["delegate_user"]
        child.has_delegation = 1
        child.idx = max_idx + 1
        child.db_insert()

        doc.add_comment(
            "Info",
            _("Level {0} delegated from {1} to {2} via Leave Delegation {3}").format(
                info["level"], info["previous_reviewer"], info["delegate_user"], info["delegation_name"]
            )
        )


def restore_delegations():
    today = frappe.utils.today()

    expired = frappe.get_all(
        "Leave Delegation",
        filters={
            "docstatus": 1,
            "is_active": 1,
            "valid_to": ["<", today],
        },
        pluck="name",
    )

    for delegation_name in expired:
        delegation = frappe.get_doc("Leave Delegation", delegation_name)

        for row in delegation.leave_delegation_detail:
            if not row.has_delegation:
                continue

            if not frappe.db.exists("Leave Application", row.document_name):
                continue

            current_approver = frappe.db.get_value("Leave Application", row.document_name, row.approver_field)

            if current_approver == row.delegate_user:
                frappe.db.set_value("Leave Application", row.document_name, row.approver_field, row.previous_reviewer)

                leave_app = frappe.get_doc("Leave Application", row.document_name)
                leave_app.add_comment(
                    "Info",
                    _("Level {0} restored from {1} to {2} (delegation expired)").format(
                        row.level, row.delegate_user, row.previous_reviewer
                    )
                )

        frappe.db.set_value("Leave Delegation", delegation_name, "is_active", 0)
