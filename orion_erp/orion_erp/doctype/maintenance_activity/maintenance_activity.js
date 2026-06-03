// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Maintenance Activity", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.vehicle) {
			frm.add_custom_button(__("Return to Service"), () => {
				frappe.call({
					method: "orion_erp.orion_erp.doctype.maintenance_activity.maintenance_activity.return_to_service",
					args: { name: frm.doc.name },
					freeze: true,
					callback: () => {
						frappe.show_alert({ message: __("Vehicle returned to service."), indicator: "green" });
					},
				});
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

// Auto-fill Customer from the vehicle's rental on the activity date.
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
