// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Traffic Fine or Accident", {
	refresh(frm) {
		// Accounts-only: when the driver is responsible, create the deduction shell.
		const is_accounts =
			frappe.user.has_role("Accounts Manager") || frappe.user.has_role("System Manager");
		if (
			frm.doc.docstatus === 1 &&
			frm.doc.closing_status === "Paid by Driver" &&
			!frm.doc.employee_deduction &&
			is_accounts
		) {
			frm.add_custom_button(__("Deduct from Employee"), () => {
				frappe.call({
					method: "orion_erp.orion_erp.doctype.traffic_fine_or_accident.traffic_fine_or_accident.create_employee_deduction",
					args: { name: frm.doc.name },
					freeze: true,
					callback: (r) => {
						if (r.message) {
							frappe.msgprint({
								title: __("Employee Deduction created"),
								message: __("Draft {0} created — add penalty rows and submit.", [
									`<a href="/app/employee-deduction/${r.message}">${r.message}</a>`,
								]),
								indicator: "green",
							});
							frm.reload_doc();
						}
					},
				});
			}).addClass("btn-primary");
		}

		if (frm.doc.docstatus === 1 && frm.doc.employee_deduction) {
			frm.add_custom_button(__("View Employee Deduction"), () => {
				frappe.set_route("Form", "Employee Deduction", frm.doc.employee_deduction);
			});
		}
	},

	vehicle(frm) {
		fill_customer_from_rental(frm);
	},

	date(frm) {
		fill_customer_from_rental(frm);
	},
});

// Auto-fill Customer (which company the fine belongs to) from the vehicle's rental
// on the fine date — so you don't have to open the Project to find it.
function fill_customer_from_rental(frm) {
	if (!frm.doc.vehicle || !frm.doc.date) return;
	frappe.call({
		method: "orion_erp.orion_erp.doctype.monthly_billing.monthly_billing.rental_customer",
		args: { vehicle: frm.doc.vehicle, on_date: frm.doc.date },
		callback: (r) => {
			if (r.message && r.message.customer) {
				frm.set_value("customer", r.message.customer);
				frm.set_value("project", r.message.project);
			}
		},
	});
}

frappe.ui.form.on("Fines cdt", {
	detail_add: function (frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (frm.doc.project) row.project = frm.doc.project;
		if (frm.doc.vehicle) row.vrn = frm.doc.vehicle;
		frm.refresh_field("detail");
	},
});

frappe.ui.form.on("Accident Logs", {
	accident_detail_add: function (frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (frm.doc.project) row.project = frm.doc.project;
		if (frm.doc.vehicle) row.vrn = frm.doc.vehicle;
		frm.refresh_field("accident_detail");
	},
});
