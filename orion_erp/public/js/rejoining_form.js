const REJOINING_APPROVAL_FLOW = [
    {
        approver_field: "custom_rejoining_approver_1",
        status_field: "custom_status_rejoining_approver1"
    },
    {
        approver_field: "custom_rejoining_approver_2",
        status_field: "custom_status_rejoining_approver2"
    },
    {
        approver_field: "custom_rejoining_approver_3",
        status_field: "custom_status_rejoining_approver3"
    },
    {
        approver_field: "custom_rejoining_approver_4",
        status_field: "custom_status_rejoining_approver4"
    },
    {
        approver_field: "custom_rejoining_approver_5",
        status_field: "custom_status_rejoining_approver5"
    }
];

frappe.ui.form.on("Rejoining Form", {
    employee(frm) {
        if (!frm.doc.employee) {
            return;
        }

        frappe.call({
            method: "orion_erp.orion_erp.validations.rejoining_form.get_employee_details",
            args: {
                employee: frm.doc.employee
            },
            callback: function(r) {
                if (!r.message) {
                    return;
                }

                let data = r.message;

                frm.set_value("employee_name", data.employee_name || "");
                frm.set_value("company", data.company || "");
                frm.set_value("department", data.department || "");
                frm.set_value("designation", data.designation || "");
                frm.set_value("custom_employee_user_id", data.user_id || "");

                frm.set_value("custom_rejoining_approver_1", data.leave_approver || "");
                frm.set_value("custom_rejoining_approver_2", data.custom_leave_approver_1 || "");
                frm.set_value("custom_rejoining_approver_3", data.custom_leave_approver_2 || "");
                frm.set_value("custom_rejoining_approver_4", data.custom_leave_approver_3 || "");
                frm.set_value("custom_rejoining_approver_5", data.custom_leave_approver_4 || "");

                frm.refresh_fields();
            }
        });
    },

    before_submit(frm) {
        validate_all_approvals(frm);
    },

    leave_application(frm) {
        if (!frm.doc.leave_application) return;

        frappe.call({
            method: "orion_erp.orion_erp.validations.rejoining_form.get_leave_application_details",
            args: { leave_application: frm.doc.leave_application },
            callback: function(r) {
                if (!r.message) return;
                let data = r.message;
                frm.set_value("employee", data.employee || "");
                frm.set_value("employee_name", data.employee_name || "");
                frm.set_value("leave_type", data.leave_type || "");
                frm.set_value("leave_start_date", data.from_date || "");
                frm.set_value("leave_end_date", data.to_date || "");
                frm.set_value("leave_days_approved", data.total_leave_days || "");
                frm.set_value("company", data.company || "");
                frm.set_value("custom_employee_user_id", data.custom_employee_user_id || "");
                frm.refresh_fields();
            }
        });
    },

    refresh(frm) {
        handle_cancel_button(frm);

        frm.set_query("leave_application", function() {
            let filters = { docstatus: 1, status: "Approved" };
            if (frm.doc.employee) {
                filters.employee = frm.doc.employee;
            }
            return { filters: filters };
        });

        let status_to_show = frm.doc.custom_rejoining_approval_status;

        if (frm.is_new() && !status_to_show) {
            frm.set_value("custom_rejoining_approval_status", "Open");
        }

        apply_custom_status_indicator(frm);
        handle_submit_button(frm);

        if (!frm.doc.employee) {
            return;
        }

        let current_user = frappe.session.user;
        let is_employee = frm.doc.custom_employee_user_id === current_user;

        function get_previous_active_status(idx) {
            for (let i = idx - 1; i >= 0; i--) {
                if (frm.doc[REJOINING_APPROVAL_FLOW[i].approver_field]) {
                    return frm.doc[REJOINING_APPROVAL_FLOW[i].status_field];
                }
            }
            return null;
        }

        REJOINING_APPROVAL_FLOW.forEach((row, index) => {
            let approver = frm.doc[row.approver_field];
            let visible = false;

            if (is_employee) {
                visible = true;
            } else if (current_user === "Administrator") {
                visible = true;
            } else if (approver === current_user) {
                if (index === 0) {
                    visible = true;
                } else {
                    let previous_status = get_previous_active_status(index);
                    if (previous_status === "Approved") {
                        visible = true;
                    }
                }
            }

            frm.toggle_display(row.approver_field, visible);
            frm.toggle_display(row.status_field, visible);

            let read_only = true;

            if (approver === current_user && !is_employee) {
                if (index === 0) {
                    read_only = false;
                } else {
                    let previous_status = get_previous_active_status(index);
                    if (previous_status === "Approved") {
                        read_only = false;
                    }
                }
            }

            if (is_employee) {
                read_only = true;
            }

            if (current_user === "Administrator") {
                read_only = false;
            }

            frm.set_df_property(row.status_field, "read_only", read_only);
            frm.set_df_property(row.approver_field, "read_only", 1);
        });

        frm.refresh_fields();
    }
});

function validate_all_approvals(frm) {
    let pending_approvals = [];

    REJOINING_APPROVAL_FLOW.forEach((row) => {
        let approver = frm.doc[row.approver_field];
        let status = frm.doc[row.status_field];

        if (approver) {
            if (status !== "Approved") {
                pending_approvals.push(row.status_field);
            }
        }
    });

    if (pending_approvals.length) {
        frappe.throw(
            __("Only Rejoining Forms with all approvers status as 'Approved' can be submitted.")
        );
    }
}

function handle_submit_button(frm) {
    let current_user = frappe.session.user;
    let can_submit = false;

    if (current_user === "Administrator") {
        can_submit = true;
    }

    let active_approvers = REJOINING_APPROVAL_FLOW.filter(
        row => frm.doc[row.approver_field]
    );

    if (active_approvers.length) {
        let last_row = active_approvers[active_approvers.length - 1];
        let last_approver = frm.doc[last_row.approver_field];

        let all_previous_approved = true;
        for (let i = 0; i < active_approvers.length - 1; i++) {
            let status = frm.doc[active_approvers[i].status_field];
            if (status !== "Approved") {
                all_previous_approved = false;
                break;
            }
        }

        let last_status = frm.doc[last_row.status_field];

        if (current_user === last_approver && all_previous_approved && last_status === "Approved") {
            can_submit = true;
        }

        active_approvers.forEach((row) => {
            let approver = frm.doc[row.approver_field];
            let status = frm.doc[row.status_field];
            if (approver === current_user && status === "Cancelled") {
                can_submit = true;
            }
        });
    }

    frm.enable_save();

    if (frm.is_new() || frm.doc.docstatus !== 0) return;

    frm.page.clear_primary_action();

    if (can_submit) {
        frm.page.set_primary_action(
            __("Submit"),
            () => frm.save("Submit")
        );
    } else {
        frm.page.set_primary_action(
            __("Save"),
            () => frm.save()
        );
    }
}

function handle_cancel_button(frm) {
    $(".btn-cancel-rejoining").remove();

    if (frm.is_new()) return;
    if (frm.doc.docstatus !== 0) return;
    if (frm.doc.custom_rejoining_approval_status === "Cancelled") return;

    let today = frappe.datetime.nowdate();

    if (frm.doc.custom_employee_user_id !== frappe.session.user && frm.doc.owner !== frappe.session.user && frappe.session.user !== "Administrator") return;

    frappe.db.get_value("Rejoining Form", frm.doc.name, "name", function(r) {
        if (!r) return;

        frm.add_custom_button(
            __("Cancel Rejoining"),
            function() {
                frappe.confirm(
                    __("Are you sure you want to cancel this rejoining form?"),
                    function() {
                        frappe.call({
                            method: "orion_erp.orion_erp.validations.rejoining_form.cancel_draft_rejoining",
                            args: { docname: frm.doc.name },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __("Rejoining form has been cancelled."),
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
    if (status === "Approved" || status === "Fully Approved") {
        return "green";
    }
    if (status === "Rejected") {
        return "red";
    }
    if (status === "Cancelled") {
        return "red";
    }
    if (status === "Open" || status.startsWith("Pending Approval") || status === "Submit Pending") {
        return "orange";
    }
    return "blue";
}

function apply_custom_status_indicator(frm) {
    let status = frm.doc.custom_rejoining_approval_status || "Open";

    frm.page.set_indicator(status, get_indicator_color(status));

    let field = frm.get_field("custom_rejoining_approval_status");
    if (field && field.$wrapper) {
        field.$wrapper.find(".control-value, .like-disabled-input")
            .removeClass("green red orange blue")
            .addClass("indicator-pill " + get_indicator_color(status));
    }
}
