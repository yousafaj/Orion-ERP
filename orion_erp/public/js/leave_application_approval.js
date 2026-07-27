const APPROVAL_FLOW = [

    {
        approver_field: "leave_approver",
        status_field: "status"
    },

    {
        approver_field: "custom_leave_approver_1",
        status_field: "custom_status_approver1"
    },

    {
        approver_field: "custom_leave_approver_2",
        status_field: "custom_status_approver2"
    },

    {
        approver_field: "custom_leave_approver_4",
        status_field: "custom_status_approver4"
    },

    {
        approver_field: "custom_leave_approver_5",
        status_field: "custom_status_approver5"
    }
];

let _cached_override_roles = null;
let _cached_override_check = null;

function is_leave_override_user(frm) {
    if (_cached_override_check !== null) {
        return _cached_override_check;
    }
    frappe.call({
        method: "orion_erp.orion_erp.validations.leave_application.get_override_roles",
        async: false,
        callback: function(r) {
            if (r.message) {
                _cached_override_roles = r.message;
                _cached_override_check = frappe.user_roles.some(
                    role => r.message.includes(role)
                );
            } else {
                _cached_override_check = false;
            }
        }
    });
    return _cached_override_check;
}


function validate_all_approvals(frm) {

    let pending_approvals = [];

    APPROVAL_FLOW.forEach((row) => {

        let approver =
            frm.doc[row.approver_field];

        let status =
            frm.doc[row.status_field];

        // Only active approvers
        if (approver) {

            if (status !== "Approved") {

                pending_approvals.push(
                    row.status_field
                );
            }
        }
    });

    // Prevent submit
    if (pending_approvals.length) {

        frappe.throw(
            __(
                "Only Leave Applications with all approvers status as 'Approved' can be submitted."
            )
        );
    }
}


function handle_submit_button(frm) {

    let current_user = frappe.session.user;

    let is_employee =
        frm.doc.custom_employee_user_id === current_user;

    let is_sent =
        frm.doc.custom_sent_for_approval || frm.doc.custom_approval_status !== "Open";

    let can_submit = false;

    if (frm.doc.custom_approval_status === "Cancelled" || frm.doc.status === "Cancelled") {
        _refresh_submit_button(frm, false, is_employee, is_sent);
        return;
    }

    if (current_user === "Administrator") {
        can_submit = true;
    }

    let active_approvers = APPROVAL_FLOW.filter(
        row => frm.doc[row.approver_field]
    );

    if (active_approvers.length) {

        let last_row =
            active_approvers[
                active_approvers.length - 1
            ];

        let last_approver =
            frm.doc[last_row.approver_field];

        let all_previous_approved = true;

        for (
            let i = 0;
            i < active_approvers.length - 1;
            i++
        ) {

            let status =
                frm.doc[
                    active_approvers[i]
                    .status_field
                ];

            if (status !== "Approved") {

                all_previous_approved = false;
                break;
            }
        }

        let last_status =
            frm.doc[last_row.status_field];

        // Last approver can submit
        if (
            current_user === last_approver &&
            all_previous_approved &&
            last_status === "Approved"
        ) {

            can_submit = true;
        }

        // All approved - override users can submit
        let all_approved = active_approvers.every(
            row => frm.doc[row.status_field] === "Approved"
        );

        if (all_approved && !can_submit) {
            let is_override = is_leave_override_user(frm);
            if (is_override) {
                can_submit = true;
            }
        }
    }

    _refresh_submit_button(frm, can_submit, is_employee, is_sent);
}

function _refresh_submit_button(frm, can_submit, is_employee, is_sent) {

    frm.page.clear_primary_action();

    if (frm.is_new()) {
        frm.enable_save();
        frm.page.set_primary_action(
            __("Save"),
            () => frm.save()
        );
        return;
    }

    if (frm.doc.docstatus !== 0) {
        frm.disable_save();
        return;
    }

    if (frm.doc.custom_approval_status === "Cancelled") {
        frm.disable_save();
        return;
    }

    // Admin / approver with submit permission
    if (can_submit) {
        frm.enable_save();
        frm.page.set_primary_action(
            __("Submit"),
            () => frm.save("Submit")
        );
        return;
    }

    // Employee with sent doc: disable save and hide actions
    if (is_employee && is_sent) {
        frm.disable_save();
        return;
    }

    // Employee with draft (not sent): Send for Approval as primary + Save enabled
    if (is_employee && !is_sent) {
        frm.enable_save();
        frm.page.set_primary_action(
            __("Send for Approval"),
            () => {
                frappe.confirm(
                    __("Are you sure you want to send this Leave Application for approval?"),
                    () => {
                        var after_save = function() {
                            frappe.call({
                                method: "orion_erp.orion_erp.validations.leave_application.send_for_approval",
                                args: { docname: frm.doc.name },
                                callback: (r) => {
                                    if (r.message) {
                                        frappe.show_alert({
                                            message: __("Leave Application has been sent for approval."),
                                            indicator: "green"
                                        });
                                        frm.reload_doc();
                                    }
                                }
                            });
                        };
                        if (frm.is_dirty()) {
                            frm.save(null, after_save);
                        } else {
                            after_save();
                        }
                    }
                );
            }
        );
        return;
    }

    // Other users (approvers): show Save
    frm.enable_save();
    frm.page.set_primary_action(
        __("Save"),
        () => frm.save()
    );
}

function handle_cancel_button(frm) {
    $(".btn-cancel-leave").remove();

    if (frm.is_new()) return;

    if (frm.doc.docstatus !== 0) return;

    if (frm.doc.status === "Cancelled") return;

    if (!frm.doc.from_date) return;

    let today = frappe.datetime.nowdate();
    if (today >= frm.doc.from_date) return;

    if (frm.doc.custom_employee_user_id !== frappe.session.user && frm.doc.owner !== frappe.session.user && frappe.session.user !== "Administrator") return;

    frappe.db.get_value("Leave Application", frm.doc.name, "name", function(r) {
        if (!r) return;

        frm.add_custom_button(
            __("Cancel Leave"),
            function() {
                frappe.confirm(
                    __("Are you sure you want to cancel this leave application?"),
                    function() {
                        frappe.call({
                            method: "orion_erp.orion_erp.validations.leave_application.cancel_draft_leave",
                            args: { docname: frm.doc.name },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __("Leave application has been cancelled."),
                                        indicator: "green"
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }
        );
    });
}
