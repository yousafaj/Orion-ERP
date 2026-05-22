// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("LEAVE DECLARATION", {

    // Fetch the passport number from Employee record
    employee: function(frm) {

        if (!frm.doc.employee) return;

        frappe.call({
            method: "rental_management.rental_management.doctype.leave_declaration.leave_declaration.get_passport_number",
            args: {
                employee: frm.doc.employee
            },
            callback: function(r) {

                // Set passport number if returned from server
                if (r.message) {
                    frm.set_value("passport_number", r.message);
                }
            }
        });

    },

    // Apply filter on Employee field to show only Active employees
    setup: function(frm) {
        frm.set_query("employee", function() {
            return {
                filters: {
                    status: "Active"
                }
            };
        });
    },

    // Recalculate leave days when start date changes
    leave_start_date: function(frm) {
        calculate_leave_days(frm);
    },

    // Recalculate leave days when end date changes
    leave_end_date: function(frm) {
        calculate_leave_days(frm);
    }
});


// Calculate total leave days between start and end date
function calculate_leave_days(frm) {

    if (frm.doc.leave_start_date && frm.doc.leave_end_date) {

        let start = frappe.datetime.str_to_obj(frm.doc.leave_start_date);
        let end = frappe.datetime.str_to_obj(frm.doc.leave_end_date);

        let diff = frappe.datetime.get_day_diff(end, start) + 1;

        // Set calculated leave days in the field
        frm.set_value("leave_days", diff);
    }
}