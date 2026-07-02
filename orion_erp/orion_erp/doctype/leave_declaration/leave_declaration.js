// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("LEAVE DECLARATION", {

    employee: function(frm) {
        if (!frm.doc.employee) return;

        frappe.call({
            method: "orion_erp.orion_erp.doctype.leave_declaration.leave_declaration.get_passport_number",
            args: { employee: frm.doc.employee },
            callback: function(r) {
                if (r.message) {
                    frm.set_value("passport_number", r.message);
                }
            }
        });
    },

    setup: function(frm) {
        frm.set_query("employee", function() {
            return {
                filters: { status: "Active" }
            };
        });

        frm.set_query("leave_type", function() {
            return {
                filters: { docstatus: 0 }
            };
        });
    },

    leave_type: function(frm) {
        if (frm.doc.employee && frm.doc.leave_type) {
            frappe.call({
                method: "orion_erp.orion_erp.doctype.leave_declaration.leave_declaration.get_leave_balance",
                args: {
                    employee: frm.doc.employee,
                    leave_type: frm.doc.leave_type,
                    date: frm.doc.leave_start_date || frappe.datetime.nowdate()
                },
                callback: function(r) {
                    frm.set_value("leave_balance_before", r.message || 0);
                }
            });
        }
    },

    leave_start_date: function(frm) {
        calculate_leave_days(frm);
        if (frm.doc.employee && frm.doc.leave_type && frm.doc.leave_start_date) {
            frappe.call({
                method: "orion_erp.orion_erp.doctype.leave_declaration.leave_declaration.get_leave_balance",
                args: {
                    employee: frm.doc.employee,
                    leave_type: frm.doc.leave_type,
                    date: frm.doc.leave_start_date
                },
                callback: function(r) {
                    frm.set_value("leave_balance_before", r.message || 0);
                }
            });
        }
    },

    leave_end_date: function(frm) {
        calculate_leave_days(frm);
    },

    rejoining_date: function(frm) {
        if (frm.doc.leave_end_date && frm.doc.rejoining_date) {
            let end = frappe.datetime.str_to_obj(frm.doc.leave_end_date);
            let rj = frappe.datetime.str_to_obj(frm.doc.rejoining_date);
            if (frappe.datetime.get_day_diff(rj, end) < 0) {
                frappe.msgprint({
                    title: __("Early Return"),
                    indicator: "orange",
                    message: __("Employee is returning early. Leave application will be adjusted accordingly."),
                    alert: true
                });
            } else if (frappe.datetime.get_day_diff(rj, end) > 0) {
                frappe.msgprint({
                    title: __("Extended Leave"),
                    indicator: "orange",
                    message: __("Employee is returning late. Extended leave application will be created."),
                    alert: true
                });
            }
        }
    }
});

function calculate_leave_days(frm) {
    if (frm.doc.leave_start_date && frm.doc.leave_end_date) {
        let start = frappe.datetime.str_to_obj(frm.doc.leave_start_date);
        let end = frappe.datetime.str_to_obj(frm.doc.leave_end_date);
        let diff = frappe.datetime.get_day_diff(end, start) + 1;
        frm.set_value("leave_days", diff);
    }
}