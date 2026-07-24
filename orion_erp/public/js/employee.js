let manual_paid_lock_date = null;
let original_doj = null;
let is_hr_manager = false;

frappe.ui.form.on('Employee', {
    custom_basic_salary: calculate_total,
    custom_hra: calculate_total,
    custom_ot_allowances: calculate_total,
    custom_food_allowances: calculate_total,
    custom_transportation_allowances: calculate_total,

    custom_basic: calculate_total_offered_salary,
    custom_house_rent_allowances: calculate_total_offered_salary,
    custom_food_allowances_fa: calculate_total_offered_salary,
    custom_other_allowances: calculate_total_offered_salary,
    custom_transportation_allowance: calculate_total_offered_salary,

    validate(frm) {
        if (!frm.doc.custom_notice_period) {
            frm.set_value("custom_notice_period", 0);
        }
    },

    designation: function (frm) {
        if (frm.doc.designation) {
            frappe.db.get_value(
                "Designation",
                frm.doc.designation,
                "custom_is_driver",
                function (r) {
                    if (r.custom_is_driver) {
                        frm.set_df_property("custom_type_of_driving_licence", "hidden", 0);
                    } else {
                        frm.set_df_property("custom_type_of_driving_licence", "hidden", 1);
                        frm.set_value("custom_type_of_driving_licence", "");
                    }
                }
            );
        }
    },

    setup(frm) {
        calculate_probation(frm);
        calculate_total(frm);

        Object.keys(frm.fields_dict).forEach(fieldname => {
            let field = frm.fields_dict[fieldname];
            if (field.df.fieldtype === "Link" && field.df.options === "User") {
                frm.set_query(fieldname, function () {
                    return {
                        query: "orion_erp.orion_erp.doctype.employee.user_by_employee"
                    };
                });
            }
        });

        if (frm.doc.designation) {
            frappe.db.get_value(
                "Designation",
                frm.doc.designation,
                "custom_is_driver",
                function (r) {
                    frm.set_df_property(
                        "custom_type_of_driving_licence",
                        "hidden",
                        r.custom_is_driver ? 0 : 1
                    );
                }
            );
        }
    },

    final_confirmation_date(frm) {
        calculate_probation(frm);
    },

    custom_probation_period(frm) {
        calculate_probation(frm);
    },

    onload: function(frm) {
        frm.set_query('custom_salary_structure', function() {
            return { filters: { docstatus: 1 } };
        });
        if (frm.doc.custom_employee_category === "Non-Office") {
            frm.set_value("final_confirmation_date", frm.doc.scheduled_confirmation_date);
        }
    },

    scheduled_confirmation_date: function(frm) {
        if (frm.doc.custom_employee_category === "Non-Office") {
            frm.set_value("final_confirmation_date", frm.doc.scheduled_confirmation_date);
        }
    },

    before_attach: function(frm) {
        if (frm.is_dirty()) {
            frm.save();
        }
    },

    refresh: function(frm) {
        let grid = frm.fields_dict.custom_ticket_allowance_detail.grid;
        grid.cannot_add_rows = true;
        grid.cannot_delete_rows = true;

        setTimeout(() => {
            grid.wrapper.find('.grid-remove-rows').hide();
            grid.wrapper.find('.grid-checkbox').hide();
        }, 100);

        frm.refresh_field("custom_ticket_allowance_detail");
        setTimeout(() => {
            frm.fields_dict.custom_notice_period.$wrapper
                .find('.control-input > input')
                .attr('readonly', true);
        }, 500);

        frm.set_query('custom_salary_structure', function() {
            return {
                filters: {
                    company: frm.doc.company,
                    custom_designation: frm.doc.designation,
                    docstatus: 1
                }
            };
        });

        let total =
            (parseFloat(frm.doc.custom_basic) || 0) +
            (parseFloat(frm.doc.custom_house_rent_allowances) || 0) +
            (parseFloat(frm.doc.custom_other_allowances) || 0) +
            (parseFloat(frm.doc.custom_food_allowances_fa) || 0) +
            (parseFloat(frm.doc.custom_transportation_allowance) || 0);

        frm.set_value("custom_total_salary_as_per_offer_letter", total);

        set_confirmation_date(frm);
        set_passport_details(frm);

        frappe.call({
            method: "orion_erp.orion_erp.doctype.employee.get_manual_paid_lock_date",
            callback: function(r) {
                manual_paid_lock_date = r.message;
            }
        });

        sort_ticket_allowance(frm);
        frappe.after_ajax(() => {
            toggle_salary_structure(frm);
        });

        if (!frm.is_new()) {
            frappe.call({
                method: "orion_erp.orion_erp.doctype.employee.can_edit_doj",
                args: { employee_name: frm.doc.name },
                callback: function(r) {
                    let result = r.message || {};
                    is_hr_manager = result.allowed === true;
                    frm.set_df_property('date_of_joining', 'read_only', is_hr_manager ? 0 : 1);
                    original_doj = frm.doc.date_of_joining;

                    if (!is_hr_manager && result.reason === "expired") {
                        frm.set_df_property('date_of_joining', 'description',
                            __('DOJ edit period expired on {0}. Only Administrator can change.', [result.expiry_date]));
                    } else if (is_hr_manager) {
                        frm.set_df_property('date_of_joining', 'description', '');
                    }
                }
            });
        }
    },

    custom_salary_structure: function(frm) {
        toggle_salary_structure(frm);
    },

    date_of_joining: function(frm) {
        if (!frm.is_new() && frm.doc.date_of_joining && original_doj &&
            frm.doc.date_of_joining !== original_doj && is_hr_manager) {
            show_doj_change_dialog(frm);
        } else {
            set_confirmation_date(frm);
            calculate_probation(frm);
            toggle_salary_structure(frm);
        }
    },

    salary_mode: function(frm) {
        if (frm.doc.salary_mode === "C3 Pay") {
            frappe.db.get_single_value('Orion Settings', 'default_bank_name_for_c3_pay')
                .then(value => {
                    if (value) {
                        frm.set_value('bank_name', value);
                    }
                });
        }
    }
});

function show_doj_change_dialog(frm) {
    frappe.call({
        method: "orion_erp.orion_erp.doctype.employee.get_active_leave_allocations_for_employee",
        args: { employee: frm.doc.name },
        callback: function(r) {
            let alloc_count = (r.message && r.message.allocations) || 0;
            let lpa_count = (r.message && r.message.leave_policy_assignments) || 0;

            let warning_html = '<div style="padding:12px;background:#fff3e0;border:1px solid #ffcc80;border-radius:4px;margin-bottom:8px;">';
            warning_html += '<b style="font-size:14px;">Date of Joining Change</b><br><br>';
            warning_html += 'Changing the Date of Joining will:<br><br>';

            if (alloc_count > 0) {
                warning_html += '• Cancel <b>' + alloc_count + '</b> active non-expired Leave Allocation(s).<br>';
            }
            if (lpa_count > 0) {
                warning_html += '• Cancel <b>' + lpa_count + '</b> active non-expired Leave Policy Assignment(s).<br>';
            }
            if (alloc_count === 0 && lpa_count === 0) {
                warning_html += '• No active non-expired Leave Allocations or Leave Policy Assignments found.<br>';
            }

            warning_html += '• Re-create accrual leave allocations for each completed month based on the new DOJ.<br>';
            warning_html += '• Re-create Leave Policy Assignment with correct dates for the new DOJ period.<br>';
            warning_html += '• Correct current year ticket allowance dates to align with the new DOJ.<br>';
            warning_html += '</div>';

            let dialog = new frappe.ui.Dialog({
                title: __('Confirm Date of Joining Change'),
                minimizable: false,
                fields: [
                    {
                        fieldname: 'warning_html',
                        fieldtype: 'HTML',
                        options: warning_html
                    }
                ],
                primary_action_label: __('Confirm'),
                primary_action: function() {
                    dialog.hide();
                    set_confirmation_date(frm);
                    calculate_probation(frm);
                    frappe.dom.freeze(__('Saving...'));
                    frm.save().then(function() {
                        frappe.dom.unfreeze();
                        frappe.show_alert({message: __('Date of Joining updated successfully'), indicator: 'green'});
                    }, function(err) {
                        frappe.dom.unfreeze();
                        let msg = (err && err.message) || __('Failed to save. Please check the form for errors.');
                        frappe.msgprint({title: __('Error'), indicator: 'red', message: msg});
                        frm.reload_doc();
                    });
                },
                secondary_action_label: __('Cancel'),
                secondary_action: function() {
                    frm.set_value('date_of_joining', original_doj);
                    dialog.hide();
                }
            });

            dialog.$wrapper.find('.modal-header .close').on('click', function() {
                frm.set_value('date_of_joining', original_doj);
                dialog.hide();
            });

            dialog.show();
        }
    });
}

function calculate_total_offered_salary(frm) {
    let total =
        (parseInt(frm.doc.custom_basic) || 0) +
        (parseInt(frm.doc.custom_house_rent_allowances) || 0) +
        (parseInt(frm.doc.custom_other_allowances) || 0) +
        (parseInt(frm.doc.custom_food_allowances_fa) || 0) +
        (parseInt(frm.doc.custom_transportation_allowance) || 0);

    if (frm.doc.custom_total_salary_as_per_offer_letter !== total) {
        frm.set_value("custom_total_salary_as_per_offer_letter", total, null, true);
        frm.dirty = false;
    }
}

function toggle_salary_structure(frm) {
    if (!frm.doc.name || !frm.doc.date_of_joining) return;

    frappe.call({
        method: "orion_erp.orion_erp.doctype.employee.check_salary_structure_assignment",
        args: {
            employee: frm.doc.name,
            doj: frm.doc.date_of_joining
        },
        callback: function(r) {
            if (r.message) {
                frm.set_df_property('custom_salary_structure', 'read_only', 1);
            } else {
                frm.set_df_property('custom_salary_structure', 'read_only', 0);
            }
        }
    });
}

function toggle_salary_structure_readonly(frm) {
    if (frm.doc.custom_salary_structure && !frm.is_new()) {
        frm.set_df_property('custom_salary_structure', 'read_only', 1);
    }
}

function set_passport_details(frm) {
    if (!frm.doc.custom_certificates) return;

    let passport_row = frm.doc.custom_certificates.find(row =>
        row.certification_name === "Passport no"
    );

    if (passport_row) {
        frm.set_value("passport_number", passport_row.reference_no);
        frm.set_value("date_of_issue", passport_row.date_of_issue);
        frm.set_value("valid_upto", passport_row.date_of_expiry);
    }
}

function set_confirmation_date(frm) {
    if (frm.doc.date_of_joining) {
        frm.set_value("final_confirmation_date", frm.doc.date_of_joining);
    }
}

function calculate_probation(frm) {
    if (frm.doc.date_of_joining && frm.doc.custom_probation_period) {
        let end_date = frappe.datetime.add_months(
            frm.doc.date_of_joining,
            frm.doc.custom_probation_period
        );
        frm.set_value("custom_probation_end_date", end_date);
    }
}

function calculate_total(frm) {
    let total =
        (parseInt(frm.doc.custom_basic_salary) || 0) +
        (parseInt(frm.doc.custom_hra) || 0) +
        (parseInt(frm.doc.custom_ot_allowances) || 0) +
        (parseInt(frm.doc.custom_food_allowances) || 0) +
        (parseInt(frm.doc.custom_transportation_allowances) || 0);

    if (frm.doc.custom_total_salary !== total) {
        frm.set_value("custom_total_salary", total);
    }
}

function calculate_total_offered_salary(frm) {
    let total =
        (parseInt(frm.doc.custom_basic) || 0) +
        (parseInt(frm.doc.custom_house_rent_allowances) || 0) +
        (parseInt(frm.doc.custom_other_allowances) || 0) +
        (parseInt(frm.doc.custom_food_allowances_fa) || 0) +
        (parseInt(frm.doc.custom_transportation_allowance) || 0);

    frm.set_value("custom_total_salary_as_per_offer_letter", total);
}

function lock_manual_paid(frm) {
    if (!frm.doc.manual_paid_check_read_only_date) return;

    let lock_date = frappe.datetime.str_to_obj(frm.doc.manual_paid_check_read_only_date);
    let grid = frm.fields_dict.custom_ticket_allowance_detail.grid;

    grid.grid_rows.forEach(row => {
        if (!row.doc.from) return;
        let row_from = frappe.datetime.str_to_obj(row.doc.from);
        if (row_from >= lock_date) {
            row.toggle_editable("manual_paid", false);
        } else {
            row.toggle_editable("manual_paid", true);
        }
    });
}

frappe.ui.form.on('Ticket Allowance Detail', {
    form_render(frm, cdt, cdn) {
        if (!manual_paid_lock_date) return;

        let row = locals[cdt][cdn];
        if (!row.from_date) return;

        let lock_dt = frappe.datetime.str_to_obj(manual_paid_lock_date);
        let row_from = frappe.datetime.str_to_obj(row.from_date);

        if (row_from >= lock_dt) {
            frm.fields_dict.custom_ticket_allowance_detail
                .grid.grid_rows_by_docname[cdn]
                .toggle_editable("manual_paid", false);
        } else {
            frm.fields_dict.custom_ticket_allowance_detail
                .grid.grid_rows_by_docname[cdn]
                .toggle_editable("manual_paid", true);
        }
    }
});

function sort_ticket_allowance(frm) {
    if (!frm.doc.custom_ticket_allowance_detail) return;

    frm.doc.custom_ticket_allowance_detail.sort(function(a, b) {
        return new Date(a.from_date) - new Date(b.from_date);
    });

    frm.refresh_field("custom_ticket_allowance_detail");
}

// frappe.ui.form.on("Ticket Allowance Detail", {
//     form_render(frm, cdt, cdn) {
//         setTimeout(() => {
//             $('.grid-delete-row').hide();
//             $('.grid-insert-row-below').hide();
//             $('.grid-insert-row').hide();
//         }, 100);

//         let row = locals[cdt][cdn];
//         if (!row.references_data) return;

//         setTimeout(() => {
//             let grid_row = frm.fields_dict
//                 .custom_ticket_allowance_detail
//                 .grid
//                 .grid_rows_by_docname[cdn];

//             if (!grid_row || !grid_row.grid_form) return;

//             let field = grid_row.grid_form.fields_dict.references;
//             if (!field) return;

//             field.$wrapper.html(row.references_data);
//         }, 200);
//     },

//     amount(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];

//         if (flt(row.amount) < flt(row.paid_amount)) {
//             frappe.throw(__("Amount cannot be less than Paid Amount"));
//         }

//         row.outstanding_amount = Math.max(
//             0,
//             flt(row.amount) - flt(row.paid_amount)
//         );

//         refresh_field("custom_ticket_allowance_detail");
//     }
// });
