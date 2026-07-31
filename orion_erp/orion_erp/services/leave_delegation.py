import frappe
from frappe import _
from frappe.utils import getdate
from collections import defaultdict

APPROVAL_FLOW = [
    {"approver_field": "leave_approver", "status_field": "status", "level": 1},
    {"approver_field": "custom_leave_approver_1", "status_field": "custom_status_approver1", "level": 2},
    {"approver_field": "custom_leave_approver_2", "status_field": "custom_status_approver2", "level": 3},
    {"approver_field": "custom_leave_approver_4", "status_field": "custom_status_approver4", "level": 4},
    {"approver_field": "custom_leave_approver_5", "status_field": "custom_status_approver5", "level": 5},
]


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
        results.extend(_find_pending_for_flow(flow, delegator_user, active_delegated, valid_from, valid_to))

    return results


def _find_pending_for_flow(flow, delegator_user, active_delegated, valid_from, valid_to):
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

    return [
        {
            "document_name": la.name,
            "level": level,
            "approver_field": approver_field,
            "previous_reviewer": delegator_user,
            "has_delegation": 1,
        }
        for la in leave_apps
    ]


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

    return bool(frappe.db.get_value("Leave Delegation", filters, "name"))


def auto_delegate_leave_application(doc, method=None):
    leave_start = doc.from_date or frappe.utils.today()

    if not hasattr(doc, '_auto_delegations'):
        doc._auto_delegations = []

    for flow in APPROVAL_FLOW:
        _check_and_delegate(doc, flow, leave_start)


def _check_and_delegate(doc, flow, leave_start):
    approver_field = flow["approver_field"]
    level = flow["level"]

    current_approver = doc.get(approver_field)
    if not current_approver:
        return

    delegation_name = frappe.db.get_value(
        "Leave Delegation",
        {
            "delegator_user": current_approver,
            "docstatus": 1,
            "is_active": 1,
            "valid_from": ["<=", leave_start],
            "valid_to": [">=", leave_start],
        },
        "name"
    )
    if not delegation_name:
        return

    delegation = frappe.get_doc("Leave Delegation", delegation_name)
    delegate_user = delegation.delegate_user
    if not delegate_user:
        return

    if doc.name and frappe.db.exists("Leave Delegation Detail", {
        "parent": delegation_name, "document_name": doc.name, "level": level,
    }):
        return

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
        _create_delegation_detail(doc, info)


def _create_delegation_detail(doc, info):
    already = frappe.db.exists("Leave Delegation Detail", {
        "parent": info["delegation_name"],
        "document_name": doc.name,
        "level": info["level"],
    })
    if already:
        return

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
        filters={"docstatus": 1, "is_active": 1, "valid_to": ["<", today]},
        pluck="name",
    )

    for delegation_name in expired:
        _restore_single_delegation(delegation_name)


def _restore_single_delegation(delegation_name):
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
