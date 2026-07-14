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



frappe.ui.form.on("Leave Application", {
    before_save(frm) {
        if (!frm.doc.custom_medical_certificate && frm.doc.leave_type) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Leave Type",
                    filters: {
                        name: frm.doc.leave_type
                    },
                    fieldname: [
                        "custom_medical_certificate_required",
                        "custom_medical_certificate_required_by"
                    ]
                },
                callback: function (r) {
                    if (
                        !r.message ||
                        !r.message.custom_medical_certificate_required
                    ) {
                        return;
                    }

                    let hrs = r.message.custom_medical_certificate_required_by;

                    let msg = __("Medical certificate is required for this leave type and has not been attached.");

                    if (hrs) {
                        msg += __(" It must be submitted within {0} hrs.", [hrs]);
                    }

                    frappe.msgprint({
                        title: __("Medical Certificate Required"),
                        indicator: "orange",
                        message: msg
                    });
                }
            });
        }
    },

    leave_type(frm) {
        if (!frm.doc.leave_type) {
            $(".medical-cert-flag").remove();
            return;
        }

        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Leave Type",
                filters: {
                    name: frm.doc.leave_type
                },
                fieldname: [
                    "custom_medical_certificate_required",
                    "custom_medical_certificate_required_by"
                ]
            },
            callback: function (r) {
                if (!r.message) return;

                let required =
                    r.message.custom_medical_certificate_required;

                let hrs =
                    r.message.custom_medical_certificate_required_by;

                // Create a minimal draft server-side (bypasses mandatory checks)
                // so the doc has a real name before the user uploads a certificate
                if (required && frm.is_new() && frm.doc.employee) {
                    frappe.call({
                        method: "orion_erp.orion_erp.validations.leave_application.create_leave_application_draft",
                        args: {
                            employee: frm.doc.employee,
                            leave_type: frm.doc.leave_type,
                            company: frm.doc.company,
                            employee_name: frm.doc.employee_name
                        },
                        callback: function(r) {
                            if (r.message) {
                                let real_name = r.message;
                                let old_name = frm.doc.name;

                                // Move local data to the real name key
                                locals[frm.doctype][real_name] = frm.doc;
                                delete locals[frm.doctype][old_name];

                                frm.doc.name = real_name;
                                frm.docname = real_name;
                                delete frm.doc.__islocal;
                            }
                        }
                    });
                }

                update_medical_certificate_badge(
                    frm,
                    required,
                    hrs
                );

                if (
                    required &&
                    !frm.doc.custom_medical_certificate
                ) {
                    let msg = __(
                        "Medical certificate is required for this leave type."
                    );

                    if (hrs) {
                        msg += __(
                            " It must be submitted within {0} hrs.",
                            [hrs]
                        );
                    }

                    frappe.msgprint({
                        title: __("Medical Certificate Required"),
                        indicator: "orange",
                        message: msg
                    });
                }
            }
        });
    },

    custom_medical_certificate(frm) {
        handle_medical_certificate_flag(frm);
    },
    employee(frm) {

        if (!frm.doc.employee) {
            return;
        }

        frappe.call({

            method:
            "orion_erp.orion_erp.validations.leave_application.get_employee_details",

            args: {
                employee: frm.doc.employee
            },

            callback: function(r) {

                if (!r.message) {
                    return;
                }

                let data = r.message;

                // EMPLOYEE DETAILS

                frm.set_value(
                    "employee_name",
                    data.employee_name || ""
                );

                frm.set_value(
                    "company",
                    data.company || ""
                );

                frm.set_value(
                    "department",
                    data.department || ""
                );

                frm.set_value(
                    "custom_employee_user_id",
                    data.user_id || ""
                );

            

                frm.set_value(
                    "custom_leave_approver_1",
                    data.custom_leave_approver_1 || ""
                );

                frm.set_value(
                    "custom_leave_approver_2",
                    data.custom_leave_approver_2 || ""
                );

                frm.set_value(
                    "custom_leave_approver_4",
                    data.custom_leave_approver_3 || ""
                );

                frm.set_value(
                    "custom_leave_approver_5",
                    data.custom_leave_approver_4 || ""
                );

                frm.refresh_fields();
            }
        });

        frm.set_query("leave_type", function() {
            return {
                query: "orion_erp.orion_erp.validations.leave_application.get_leave_types_for_employee",
                filters: { employee: frm.doc.employee }
            };
        });
    },
    before_submit(frm) {

        validate_all_approvals(frm);
    },
    leave_balance(frm) {
        set_leave_balance_after(frm);
    },
    total_leave_days(frm) {
        set_leave_balance_after(frm);
    },
    refresh(frm) {
        handle_cancel_button(frm);

        let status_to_show =
            frm.doc.custom_approval_status;

        if (
            frm.is_new() &&
            !status_to_show
        ) {
            frm.set_value(
                "custom_approval_status",
                "Open"
            );
        }

        apply_custom_status_indicator(frm);

        handle_medical_certificate_flag(frm);
        handle_eligibility_warnings_badge(frm);

        frm.set_query("leave_type", function() {
            return {
                query: "orion_erp.orion_erp.validations.leave_application.get_leave_types_for_employee",
                filters: { employee: frm.doc.employee }
            };
        });

        if (!frm.doc.employee) {
            return;
        }

        let current_user =
            frappe.session.user;

        let is_employee =
            frm.doc.custom_employee_user_id === current_user;

        handle_submit_button(frm);

        if (frm.doc.custom_sent_for_approval && is_employee && !frm.is_new()) {
            frm.disable_save();
            frm.page.clear_primary_action();

            let is_override = is_leave_override_user(frm);
            if (!is_override) {
                frm.fields.forEach(function(field) {
                    if (field.df.fieldname && !field.df.read_only) {
                        frm.set_df_property(field.df.fieldname, "read_only", 1);
                    }
                });
            }
            frm.set_df_property("custom_medical_certificate", "read_only", 0);
        }

        function get_previous_active_status(idx) {
            for (let i = idx - 1; i >= 0; i--) {
                if (frm.doc[APPROVAL_FLOW[i].approver_field]) {
                    return frm.doc[APPROVAL_FLOW[i].status_field];
                }
            }
            return null;
        }

        let is_override = is_leave_override_user(frm);

        APPROVAL_FLOW.forEach((row, index) => {

            let approver =
                frm.doc[row.approver_field];

            let visible = false;


            if (is_employee) {

                visible = true;

            } else if (
                current_user === "Administrator"
            ) {

                visible = true;


            } else if (is_override) {

                visible = true;

            } else if (
                approver === current_user
            ) {

                // First approver
                if (index === 0) {

                    visible = true;

                // Next approvers
                } else {

                    let previous_status =
                        get_previous_active_status(index);

                    if (
                        previous_status === "Approved"
                    ) {

                        visible = true;
                    }
                }
            }


            frm.toggle_display(
                row.approver_field,
                visible
            );

            frm.toggle_display(
                row.status_field,
                visible
            );

            let read_only = true;

            // Override users can edit any status
            if (is_override && !is_employee) {

                read_only = false;

            // Only current approver editable
            } else if (
                approver === current_user &&
                !is_employee
            ) {

                // First approver
                if (index === 0) {

                    read_only = false;

                // Next approvers
                } else {

                    let previous_status =
                        get_previous_active_status(index);

                    if (
                        previous_status === "Approved"
                    ) {

                        read_only = false;
                    }
                }
            }

            // Employee always readonly
            if (is_employee) {

                read_only = true;
            }

            // Administrator editable
            if (
                current_user === "Administrator"
            ) {

                read_only = false;
            }
            frm.set_df_property(
                row.status_field,
                "read_only",
                read_only
            );

            // Approver fields always readonly
            frm.set_df_property(
                row.approver_field,
                "read_only",
                1
            );

        });

        set_leave_balance_after(frm);
        frm.refresh_fields();
    }
});


function handle_eligibility_warnings_badge(frm) {
    $(".eligibility-warning-flag").remove();

    if (frm.doc.custom_eligibility_warnings) {
        let badge = `
        <span
            class="eligibility-warning-flag indicator-pill orange"
            style="
                margin-left:8px;
                white-space:nowrap;
                display:inline-flex;
                align-items:center;
                cursor: pointer;
            "
            title="${__(frm.doc.custom_eligibility_warnings)}"
        >
            ${__("Eligibility Warning")}
        </span>
    `;
        function tryInsertBadge() {
            if ($(".eligibility-warning-flag").length) return;
            let indicator = $(frm.page.wrapper)
                .find(".indicator-pill")
                .not(".medical-cert-flag")
                .not(".eligibility-warning-flag")
                .first();
            if (indicator.length) {
                indicator.after(badge);
                $(".eligibility-warning-flag").on("click", function() {
                    frappe.msgprint({
                        title: __("Eligibility Warnings"),
                        indicator: "orange",
                        message: frm.doc.custom_eligibility_warnings
                    });
                });
            }
        }
        tryInsertBadge();
    }
}


function handle_medical_certificate_flag(frm) {

    $(".medical-cert-flag").remove();

    if (!frm.doc.leave_type) return;

    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Leave Type",
            filters: {
                name: frm.doc.leave_type
            },
            fieldname: [
                "custom_medical_certificate_required",
                "custom_medical_certificate_required_by"
            ]
        },
        callback: function (r) {

            if (!r.message) return;

            update_medical_certificate_badge(
                frm,
                r.message.custom_medical_certificate_required,
                r.message.custom_medical_certificate_required_by
            );
        }
    });
}


function update_medical_certificate_badge(frm, required, hrs) {

    $(".medical-cert-flag").remove();

    if (
        !required ||
        frm.doc.custom_medical_certificate
    ) {
        return;
    }

    let label = __("Med. Cert Pending");

    let badge = `
    <span
        class="medical-cert-flag indicator-pill orange"
        style="
            margin-left:8px;
            white-space:nowrap;
            display:inline-flex;
            align-items:center;
        "
    >
        ${label}
    </span>
`;

    function tryInsertBadge() {

        if ($(".medical-cert-flag").length) return;

        let indicator = $(frm.page.wrapper)
            .find(".indicator-pill")
            .not(".medical-cert-flag")
            .first();

        if (indicator.length) {
            indicator.after(badge);
        }
    }

    tryInsertBadge();
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


function get_indicator_color(status) {

    if (
        status === "Approved" ||
        status === "Fully Approved"
    ) {

        return "green";
    }

    if (
        status === "Rejected"
    ) {

        return "red";
    }

    if (
        status === "Cancelled"
    ) {

        return "red";
    }

    if (
        status === "Open" ||
        status.startsWith("Pending Approval") ||
        status === "Submit Pending"
    ) {

        return "orange";
    }

    return "blue";
}

function apply_custom_status_indicator(frm) {

    let status =
        frm.doc.custom_approval_status || "Open";

    frm.page.set_indicator(
        status,
        get_indicator_color(status)
    );

    let field = frm.get_field("custom_approval_status");
    if (field && field.$wrapper) {
        field.$wrapper.find(".control-value, .like-disabled-input")
            .removeClass("green red orange blue")
            .addClass("indicator-pill " + get_indicator_color(status));
    }
}

function set_leave_balance_after(frm) {
    let balance = flt(frm.doc.leave_balance);
    let days = flt(frm.doc.total_leave_days);
    if (balance && days) {
        frm.set_value("custom_leave_balance_after", balance - days);
    } else if (balance) {
        frm.set_value("custom_leave_balance_after", balance);
    } else {
        frm.set_value("custom_leave_balance_after", 0);
    }
}