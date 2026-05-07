// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Deduction", {
	refresh(frm) {
        frm.get_field('outstanding_employee_deduction_detail').grid.cannot_add_rows = true;

        // Hide Add Row button
        frm.get_field('outstanding_employee_deduction_detail').grid.wrapper
            .find('.grid-add-row').hide();

        // Hide Delete (Remove row) button
        frm.get_field('outstanding_employee_deduction_detail').grid.wrapper
            .find('.grid-remove-rows').hide();

        
	},

    employee: function(frm) {

        if (!frm.doc.employee) return;

        frappe.call({
            method: "rental_management.rental_management.doctype.employee_deduction.employee_deduction.get_outstanding_penalties",
            args: {
                employee: frm.doc.employee
            },
            callback: function(r) {

                frm.clear_table("outstanding_employee_deduction_detail");

                (r.message || []).forEach(d => {

                    let row = frm.add_child("outstanding_employee_deduction_detail");

                    Object.keys(d).forEach(field => {
                        row[field] = d[field];
                    });

                });

                frm.refresh_field("outstanding_employee_deduction_detail");
            }
        });
    }
});
