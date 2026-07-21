// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rejoining Form", {
    leave_start_date: function(frm) {
        calculate_leave_days(frm);
    },

    leave_end_date: function(frm) {
        calculate_leave_days(frm);
    }
});

function calculate_leave_days(frm) {
    if (frm._populating_from_la) return;
    if (!frm.doc.leave_start_date || !frm.doc.leave_end_date || !frm.doc.leave_type || !frm.doc.employee) {
        return;
    }

    frappe.call({
        method: "orion_erp.orion_erp.validations.leave_application.patched_get_number_of_leave_days",
        args: {
            employee: frm.doc.employee,
            leave_type: frm.doc.leave_type,
            from_date: frm.doc.leave_start_date,
            to_date: frm.doc.leave_end_date
        },
        callback: function(r) {
            if (r.message !== undefined && r.message !== null) {
                frm.set_value("leave_days_approved", r.message);
            }
        }
    });
}
