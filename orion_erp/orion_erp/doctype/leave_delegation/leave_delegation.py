import frappe
from frappe import _
from frappe.model.document import Document

APPROVAL_FLOW = [
    {"approver_field": "leave_approver", "status_field": "status", "level": 1},
    {"approver_field": "custom_leave_approver_1", "status_field": "custom_status_approver1", "level": 2},
    {"approver_field": "custom_leave_approver_2", "status_field": "custom_status_approver2", "level": 3},
    {"approver_field": "custom_leave_approver_4", "status_field": "custom_status_approver4", "level": 4},
    {"approver_field": "custom_leave_approver_5", "status_field": "custom_status_approver5", "level": 5},
]


class LeaveDelegation(Document):
    def validate(self):
        if self.delegator_user == self.delegate_user:
            frappe.throw(_("Delegator and Delegate cannot be the same user"))
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            frappe.throw(_("Valid From must be before Valid To"))

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


@frappe.whitelist()
def get_pending_workflows(delegator):
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

        filters = {
            "docstatus": 0,
            approver_field: delegator_user,
            status_field: "Open",
        }

        if active_delegated:
            filters["name"] = ["not in", active_delegated]

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
