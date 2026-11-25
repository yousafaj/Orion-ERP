// Client Script: DocType = Vehicle, Enabled = on.
// Adds a "Vehicle Movement" button and a one-line "current driver" headline.

frappe.ui.form.on("Vehicle", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Vehicle Movement"), () => {
			frappe.set_route("query-report", "Vehicle Movement Report", { vehicle: frm.doc.name });
		});

		frappe.db
			.get_list("Vehicle Deployment", {
				filters: { vehicle: frm.doc.name, status: "Mobilized", docstatus: ["<", 2] },
				fields: ["driver_name", "customer", "site", "site_location", "mobilization_date"],
				limit: 1,
			})
			.then((r) => {
				if (!r.length) {
					frm.dashboard.set_headline(__("Free: no active deployment"), "green");
					return;
				}
				const d = r[0];
				frm.dashboard.set_headline(
					`<b>Driver:</b> ${d.driver_name || "-"} &nbsp; <b>Client:</b> ${d.customer || "-"} &nbsp; ` +
						`<b>Site:</b> ${d.site || ""} ${d.site_location || ""} &nbsp; ` +
						`<b>Since:</b> ${frappe.datetime.str_to_user(d.mobilization_date)}`,
					"blue"
				);
			});
	},
});