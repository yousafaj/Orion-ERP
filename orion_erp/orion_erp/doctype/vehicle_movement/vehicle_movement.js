// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

const VM = "orion_erp.orion_erp.doctype.vehicle_movement.vehicle_movement";

frappe.ui.form.on("Vehicle Movement", {
	project_to(frm) {
		// Auto-fill Customer from the project (editable).
		if (!frm.doc.project_to || frm.doc.customer) return;
		frappe.db.get_value("Project", frm.doc.project_to, "customer").then((r) => {
			if (r && r.message && r.message.customer) frm.set_value("customer", r.message.customer);
		});
	},

	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;

		if (frm.doc.rental_status === "Active") {
			const in_workshop = (frm.doc.off_hire || []).some((r) => !r.to_date);

			frm.add_custom_button(__("Demobilize"), () => {
				prompt_date(frm, __("Demobilize Vehicle"), "demobilize", "demobilize_date");
			});

			if (in_workshop) {
				frm.add_custom_button(__("Back in Service"), () => {
					prompt_date(frm, __("Return from Workshop"), "back_in_service", "to_date");
				});
			} else {
				frm.add_custom_button(__("To Workshop"), () => {
					prompt_date(frm, __("Send to Workshop"), "to_workshop", "from_date");
				});
			}
		}
	},
});

function prompt_date(frm, title, method, arg) {
	frappe.prompt(
		[{ fieldname: "d", label: __("Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() }],
		(v) => {
			const args = { name: frm.doc.name };
			args[arg] = v.d;
			frappe.call({ method: `${VM}.${method}`, args, freeze: true, callback: () => frm.reload_doc() });
		},
		title,
		__("Confirm")
	);
}
