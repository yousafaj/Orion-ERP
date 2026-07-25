import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, add_days, add_months

from .notifications import (
    _notify_rejected,
    _notify_cancelled,
    _notify_medical_certificate_pending,
    _is_medical_certificate_pending,
)
from .sandwich import get_sandwich_additional_days, _sandwich_applies_for_employee


APPROVAL_FLOW = [

    {
        "approver_field": "leave_approver",
        "status_field": "status"
    },

    {
        "approver_field": "custom_leave_approver_1",
        "status_field": "custom_status_approver1"
    },

    {
        "approver_field": "custom_leave_approver_2",
        "status_field": "custom_status_approver2"
    },

    {
        "approver_field": "custom_leave_approver_4",
        "status_field": "custom_status_approver4"
    },

    {
        "approver_field": "custom_leave_approver_5",
        "status_field": "custom_status_approver5"
    }
]


def is_leave_override_user(user=None):
    if not user:
        user = frappe.session.user
    if user == "Administrator":
        return True
    override_roles = frappe.get_all(
        "Role Details",
        filters={"parent": "Orion Settings", "parentfield": "leave_override_roles"},
        pluck="role"
    )
    if not override_roles:
        return False
    user_roles = frappe.get_roles(user)
    return bool(set(override_roles) & set(user_roles))


# =========================================================
# VALIDATION
# =========================================================

def validate_leave_approval(doc, method=None):

    # Allow draft creation for medical cert upload without validation
    if frappe.flags.get("creating_leave_draft"):
        return

    current_user = frappe.session.user

    # Prevent direct submission unless all active approvers have approved
    old_doc = doc.get_doc_before_save()
    if old_doc and old_doc.docstatus == 0 and doc.docstatus == 1:
        statuses = []
        for row in APPROVAL_FLOW:
            approver = doc.get(row["approver_field"])
            status = doc.get(row["status_field"])
            if approver:
                statuses.append(status)
        all_approved = all(s == "Approved" for s in statuses)
        if not all_approved:
            frappe.throw(
                _("Leave Application cannot be submitted until all approvers have approved it.")
            )

    old_doc = doc.get_doc_before_save()

    if not old_doc or (old_doc.docstatus == 2 and doc.docstatus == 0 and not doc.amended_from):
        if not doc.custom_last_status_change:
            doc.custom_last_status_change = now_datetime()
        doc.custom_approval_status = "Open"
        doc.status = "Open"
        doc.custom_status_approver1 = "Open"
        doc.custom_status_approver2 = "Open"
        doc.custom_status_approver4 = "Open"
        doc.custom_status_approver5 = "Open"
        doc.custom_reminder_sent = 0
        doc.custom_escalation_sent = 0
        return

    if current_user == "Administrator":
        return

    # Allow the send_for_approval flow
    if frappe.flags.get("in_send_for_approval"):
        return

    # If sent for approval, employee cannot edit (unless cancelling all statuses)
    if doc.custom_sent_for_approval and doc.custom_employee_user_id == current_user:
        all_cancelled = all(
            doc.get(row["status_field"]) == "Cancelled"
            for row in APPROVAL_FLOW
            if doc.get(row["approver_field"])
        )
        if not all_cancelled:
            frappe.throw(
                _("You cannot modify this Leave Application as it has been sent for approval.")
            )

    for idx, row in enumerate(APPROVAL_FLOW):

        approver = doc.get(
            row["approver_field"]
        )

        status_field = row["status_field"]

        old_value = old_doc.get(status_field)

        new_value = doc.get(status_field)

        # Status changed
        if old_value != new_value:

            # Non-override users can only update their own level
            if not is_leave_override_user():
                if approver != current_user:
                    frappe.throw(
                        _("You are not allowed to update {0}")
                        .format(status_field)
                    )

            # All users (including override) must follow sequential order
            if new_value == "Approved":
                status_labels = [
                    "Status Approver1",
                    "Status Approver2",
                    "Status Approver3",
                    "Status Approver4",
                    "Status Approver5",
                ]
                for prev_idx in range(idx):
                    prev_row = APPROVAL_FLOW[prev_idx]
                    prev_approver = doc.get(prev_row["approver_field"])
                    if prev_approver:
                        prev_status = doc.get(prev_row["status_field"])
                        if prev_status != "Approved":
                            frappe.throw(
                                _("You cannot approve {0} until {1} is Approved.")
                                .format(status_labels[idx], status_labels[prev_idx])
                            )



# =========================================================
# HANDLE APPROVAL
# =========================================================
def handle_leave_approval(doc, method=None):

    if frappe.flags.get("submitting_leave_from_rejoining"):
        return

    old_doc = doc.get_doc_before_save()
    status_changed = False

    # Track status changes for auto-escalation
    if old_doc:
        for row in APPROVAL_FLOW:
            status_field = row["status_field"]
            if old_doc.get(status_field) != doc.get(status_field):
                status_changed = True
                break
        if status_changed:
            doc.db_set("custom_last_status_change", now_datetime())
            doc.db_set("custom_reminder_sent", 0)
            doc.db_set("custom_escalation_sent", 0)

    statuses = []

    for row in APPROVAL_FLOW:

        approver = doc.get(
            row["approver_field"]
        )

        status = doc.get(
            row["status_field"]
        )

        # Only active approvers
        if approver:

            statuses.append(status)

    # If not yet sent for approval, only process cancellations
    if not doc.custom_sent_for_approval:
        if "Cancelled" not in statuses:
            return


    # REJECTED
    if "Rejected" in statuses:

        if doc.docstatus != 0:

            frappe.db.set_value(
                doc.doctype,
                doc.name,
                "docstatus",
                0
            )

        update_leave_application_status(doc)
        _notify_rejected(doc, old_doc)
        return


    # CANCELLED
    if "Cancelled" in statuses:

        if doc.docstatus != 2:

            frappe.db.set_value(
                doc.doctype,
                doc.name,
                "docstatus",
                2
            )

        doc.db_set("status", "Cancelled")
        doc.db_set("custom_last_status_change", now_datetime())
        doc.db_set("custom_reminder_sent", 0)

        for row in APPROVAL_FLOW:
            if doc.get(row["approver_field"]):
                doc.db_set(row["status_field"], "Cancelled")

        doc.db_set("custom_approval_status", "Cancelled")

        _notify_cancelled(doc, old_doc)

        # Cancel linked Leave Declaration
        if not frappe.flags.get("cancelling_from_leave_declaration"):
            _cancel_linked_leave_declaration(doc.name)
        return

    # ALL APPROVED
    all_approved = all(
        status == "Approved"
        for status in statuses
    )

    if all_approved:

        update_leave_application_status(doc)

        if doc.docstatus != 1:
            if _is_medical_certificate_pending(doc):
                _notify_medical_certificate_pending(doc)
            doc.flags.ignore_permissions = True
            frappe.flags.ignore_permissions = True
            doc.submit()

        return

    if status_changed:
        from .notifications import send_next_approval_email
        send_next_approval_email(doc)

    update_leave_application_status(doc)


# =========================================================
# UPDATE STATUS
# =========================================================

def update_leave_application_status(doc):

    active_flow = []

    for flow_idx, row in enumerate(APPROVAL_FLOW):

        approver = doc.get(row["approver_field"])
        status = doc.get(row["status_field"])

        if approver:

            active_flow.append({
                "approver_field": row["approver_field"],
                "status": status,
                "level": flow_idx + 1
            })

    # =====================================================
    # REJECTED
    # =====================================================

    for row in active_flow:

        if row["status"] == "Rejected":

            doc.db_set(
                "custom_approval_status",
                "Rejected"
            )

            return

    # =====================================================
    # CANCELLED
    # =====================================================

    for row in active_flow:

        if row["status"] == "Cancelled":

            doc.db_set(
                "custom_approval_status",
                "Cancelled"
            )

            return

    last_approved = None

    for row in active_flow:

        if row["status"] == "Approved":

            last_approved = row["approver_field"]

        else:
            break

    # =====================================================
    # FULLY APPROVED
    # =====================================================

    all_approved = all(
        row["status"] == "Approved"
        for row in active_flow
    )

    if all_approved:

        doc.db_set(
            "custom_approval_status",
            "Submit Pending"
        )

        return

    # =====================================================
    # PARTIAL APPROVAL
    # =====================================================

    if last_approved:

        for idx, row in enumerate(active_flow):
            if row["status"] != "Approved":
                doc.db_set(
                    "custom_approval_status",
                    f"Pending Approval from Approver {row['level']}"
                )
                return

    # =====================================================
    # DEFAULT
    # =====================================================

    doc.db_set(
        "custom_approval_status",
        "Pending Approval from Approver 1"
    )


# =========================================================
# ON SUBMIT
# =========================================================
def on_submit_leave_application(doc, method=None):

    doc.db_set(
        "custom_approval_status",
        "Approved"
    )

    leave_balance_after = flt(doc.leave_balance) - flt(doc.total_leave_days)
    doc.db_set(
        "custom_leave_balance_after",
        leave_balance_after
    )

    additional = get_sandwich_additional_days(doc.leave_type, doc.from_date, doc.to_date, doc.employee)
    if additional:
        day_names = []
        orion_settings = frappe.get_single("Orion Settings")
        if orion_settings.get("enable_sandwich_leave") and _sandwich_applies_for_employee(doc.employee):
            lt = frappe.get_cached_doc("Leave Type", doc.leave_type)
            configured_days = [d.weekday for d in (lt.get("custom_sandwich_days") or []) if d.weekday]
            from_date = getdate(doc.from_date)
            to_date = getdate(doc.to_date)
            range_days = (to_date - from_date).days
            if "Saturday" in configured_days and (4 - from_date.weekday()) % 7 <= range_days:
                day_names.append("Saturday")
            if "Sunday" in configured_days and (0 - from_date.weekday()) % 7 <= range_days:
                day_names.append("Sunday")
        if day_names:
            frappe.msgprint(
                _("Sandwich Leave: {0} will also be deducted as per sandwich leave policy.").format(
                    " and ".join(day_names)
                ),
                indicator="orange",
                alert=True
            )


def on_cancel_leave_application(doc, method=None):

    doc.db_set(
        "custom_approval_status",
        "Cancelled"
    )

    doc.db_set(
        "custom_leave_balance_after",
        0
    )

    # Cancel linked Leave Declaration if not already being cancelled from LD
    if not frappe.flags.get("cancelling_from_leave_declaration"):
        _cancel_linked_leave_declaration(doc.name)


def _cancel_linked_leave_declaration(la_name):
    """Cancel the Leave Declaration linked to this Leave Application."""
    ld_name = frappe.db.get_value(
        "LEAVE DECLARATION",
        {"leave_application": la_name, "docstatus": 1},
        "name"
    )
    if ld_name:
        frappe.flags.cancelling_from_leave_declaration = True
        try:
            ld_doc = frappe.get_doc("LEAVE DECLARATION", ld_name)
            ld_doc.flags.ignore_permissions = True
            ld_doc.cancel()
        finally:
            frappe.flags.cancelling_from_leave_declaration = False


def reset_status_on_amend(doc, method=None):
    if not doc.amended_from:
        return

    if doc.get_doc_before_save():
        return

    doc.status = "Open"
    doc.custom_status_approver1 = "Open"
    doc.custom_status_approver2 = "Open"
    doc.custom_status_approver4 = "Open"
    doc.custom_status_approver5 = "Open"
    doc.custom_approval_status = "Open"
    doc.custom_last_status_change = now_datetime()
    doc.custom_reminder_sent = 0
    doc.custom_escalation_sent = 0
