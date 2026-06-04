// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

const FINE = "orion_erp.orion_erp.doctype.traffic_fine_or_accident.traffic_fine_or_accident";

frappe.ui.form.on("Traffic Fine or Accident", {
	refresh(frm) {
		const is_accounts =
			frappe.user.has_role("Accounts Manager") || frappe.user.has_role("System Manager");
		if (frm.doc.docstatus === 1 && frm.doc.closing_status === "Paid by Driver" && !frm.doc.employee_deduction && is_accounts) {
			frm.add_custom_button(__("Deduct from Employee"), () => {
				frappe.call({
					method: `${FINE}.create_employee_deduction`,
					args: { name: frm.doc.name },
					freeze: true,
					callback: (r) => {
						if (r.message) {
							frappe.msgprint({
								title: __("Employee Deduction created"),
								message: __("Draft {0} created — add penalty rows and submit.", [r.message]),
								indicator: "green",
							});
							frm.reload_doc();
						}
					},
				});
			}).addClass("btn-primary");
		}
		if (frm.doc.docstatus === 1 && frm.doc.employee_deduction) {
			frm.add_custom_button(__("View Employee Deduction"), () =>
				frappe.set_route("Form", "Employee Deduction", frm.doc.employee_deduction)
			);
		}
	},

	vehicle(frm) {
		fill_customer(frm);
	},
	date(frm) {
		fill_customer(frm);
	},
});

function fill_customer(frm) {
	if (!frm.doc.vehicle || !frm.doc.date) return;
	frappe.call({
		method: "orion_erp.orion_erp.doctype.monthly_billing.monthly_billing.rental_customer",
		args: { vehicle: frm.doc.vehicle, on_date: frm.doc.date },
		callback: (r) => {
			if (r.message && r.message.customer) frm.set_value("customer", r.message.customer);
		},
	});
}
