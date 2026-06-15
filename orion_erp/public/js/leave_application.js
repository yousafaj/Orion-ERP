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
    refresh(frm) {
        handle_cancel_button(frm);

        let status_to_show = frm.doc.custom_approval_status;

        if (frm.is_new() && !status_to_show) {
            status_to_show = "Open";
            frm.set_value("custom_approval_status", "Open");
        }

        if (status_to_show) {
            frm.page.set_indicator(
                status_to_show,
                get_indicator_color(status_to_show)
            );
        }

        frappe.dom.set_style(
            '.frappe-control[data-fieldname="custom_approval_status"] .control-value, \
             .frappe-control[data-fieldname="custom_approval_status"] .like-disabled-input, \
             .page-head .indicator-pill { \
                max-width: none !important; \
                min-width: 140px !important; \
                white-space: nowrap !important; \
                overflow: visible !important; \
                text-overflow: clip !important; \
                width: auto !important; \
            }'
        );

        handle_submit_button(frm);
        handle_medical_certificate_flag(frm);

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


            } else if (
                approver === current_user
            ) {

                // First approver
                if (index === 0) {

                    visible = true;

                // Next approvers
                } else {

                    let previous_status =
                        frm.doc[
                            APPROVAL_FLOW[index - 1]
                            .status_field
                        ];

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

            // Only current approver editable
            if (
                approver === current_user &&
                !is_employee
            ) {

                // First approver
                if (index === 0) {

                    read_only = false;

                // Next approvers
                } else {

                    let previous_status =
                        frm.doc[
                            APPROVAL_FLOW[index - 1]
                            .status_field
                        ];

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

        frm.refresh_fields();
    }
});


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

    let can_submit = false;

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

        // Cancelled approver can submit
        active_approvers.forEach((row) => {

            let approver =
                frm.doc[row.approver_field];

            let status =
                frm.doc[row.status_field];

            if (
                approver === current_user &&
                status === "Cancelled"
            ) {

                can_submit = true;
            }
        });
    }

    // Always allow save
    frm.enable_save();

    // Hide only submit button
    if (
        !can_submit &&
        !frm.is_new() &&
        frm.doc.docstatus === 0
    ) {

        frm.page.clear_primary_action();

        frm.page.set_primary_action(
            __("Save"),
            () => frm.save()
        );
    }
}

function handle_cancel_button(frm) {
    $(".btn-cancel-leave").remove();

    if (frm.is_new()) return;

    if (frm.doc.docstatus !== 0) return;

    if (frm.doc.status === "Cancelled") return;

    if (!frm.doc.from_date) return;

    let today = frappe.datetime.nowdate();
    if (today >= frm.doc.from_date) return;

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
        status === "Open"
    ) {

        return "orange";
    }

    return "blue";
}