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
            method: "orion_erp.orion_erp.doctype.employee_deduction.employee_deduction.get_outstanding_penalties",
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
frappe.ui.form.on("Employee Deduction Detail", {
	deduction_amount(frm, cdt, cdn) {
		calculate_installment_amount(cdt, cdn);
	},

	installment(frm, cdt, cdn) {
		calculate_installment_amount(cdt, cdn);
	}
});

function calculate_installment_amount(cdt, cdn) {
	let row = locals[cdt][cdn];

	if (row.deduction_amount && row.installment) {
		row.installment_amount = flt(row.deduction_amount) / flt(row.installment);
		refresh_field("installment_amount");
	}
}
frappe.ui.form.on("Outstanding Employee Deduction Detail", {
    form_render(frm, cdt, cdn) {

        setTimeout(() => {

            // hide delete button inside row form
            $('.grid-delete-row').hide();

            // hide insert below/above
            $('.grid-insert-row-below').hide();
            $('.grid-insert-row').hide();

        }, 100);
    }
});
