// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Orion Settings", {
	trigger_oe_cron(frm) {

        frappe.call({
            method: "orion_erp.doctype.employee_deduction.employee_deduction.run_deduction_cron",
            freeze: true,
            freeze_message: __("Processing..."),
            callback: function(r) {
                frappe.msgprint("Cron Executed Successfully");
            }
        });

    },
    show_trigger_additional_deduction_office(frm) {
		frm.save();
	},

	show_trigger_additional_deduction_non_office(frm) {
		frm.save();
	},
    trigger_additional_deduction_for_office_employee(frm) {

		frappe.call({
			method: "orion_erp.doctype.employee_deduction.employee_deduction.run_deduction_manual",
			args: {
				employee_type: "Office"
			},
			freeze: true,
			freeze_message: "Processing Office Deductions...",
			callback: function() {
				frm.reload_doc();
			}
		});

	},

	trigger_addtional_deduction_for_non_office_employee(frm) {

		frappe.call({
			method: "orion_erp.doctype.employee_deduction.employee_deduction.run_deduction_manual",
			args: {
				employee_type: "Non-Office"
			},
			freeze: true,
			freeze_message: "Processing Non-Office Deductions...",
			callback: function() {
				frm.reload_doc();
			}
		});

	}
});


frappe.ui.form.on('Ticket Entitlement', {
    designation_selector: function(frm, cdt, cdn) {

        let row = locals[cdt][cdn];

        // get already selected designations
        let existing = [];
        if (row.designations) {
            existing = row.designations.split(',').map(d => d.trim());
        }

        const dialog = new frappe.ui.Dialog({
            title: "Select Designations",
            fields: [
                {
                    fieldname: "designations",
                    label: "Designations",
                    fieldtype: "MultiSelectList",
                    get_data: function(txt) {
                        return frappe.db.get_link_options("Designation", txt);
                    },
                    default: existing
                }
            ],
            primary_action_label: "Set",
            primary_action(values) {

                let selected = values.designations || [];

                // merge previous + new
                let merged = Array.from(new Set([...existing, ...selected]));

                frappe.model.set_value(
                    cdt,
                    cdn,
                    "designations",
                    merged.join(", ")
                );

                dialog.hide();
            }
        });

        dialog.show();
    }
});