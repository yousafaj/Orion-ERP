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
    employee(frm) {

        if (!frm.doc.employee) {
            return;
        }

        frappe.call({

            method:
            "rental_management.rental_management.validations.leave_application.get_employee_details",

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
    },
    before_submit(frm) {

        validate_all_approvals(frm);
    },
    refresh(frm) {
        handle_submit_button(frm);
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