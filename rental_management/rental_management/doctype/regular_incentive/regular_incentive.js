// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("REGULAR INCENTIVE", {
	// refresh(frm) {

	// },
    setup: function(frm) {
        frm.set_query("employee", function() {
            return {
                filters: {
                    status: "Active"
                }
            };
        });
        frm.set_query("from", function() {
            return {
                query: "frappe.core.doctype.user.user.user_query",
                filters: {
                    role: "HR Manager"
                }
            };
        });
    },
    employee: function(frm) {

        if (!frm.doc.employee) return;

        frappe.db.get_doc('Employee', frm.doc.employee).then(emp => {

            // clear existing rows
            frm.clear_table("details");

            let rows = [
                {
                    particulars: "Basic Salary",
                    existing: emp.custom_basic_salary
                },
                {
                    particulars: "HR Allowance",
                    existing: emp.custom_hra
                },
                {
                    particulars: "Transportation Allowance",
                    existing: emp.custom_transportation_allowances
                },
                {
                    particulars: "Other Allowance",
                    existing: emp.custom_ot_allowances
                }
            ];

            rows.forEach(d => {
                let row = frm.add_child("details");
                row.particulars = d.particulars;
                row.existing = d.existing;
            });

            frm.refresh_field("details");

        });

    },
    validate(frm) {

        let total_existing = 0;
        let total_revised = 0;

        (frm.doc.details || []).forEach(row => {

            total_existing += flt(row.existing);
            total_revised += flt(row.revised);

        });

        frm.set_value("total_existing_monthly_salary", total_existing);
        frm.set_value("total_revised_monthly_salary", total_revised);
    }
});
