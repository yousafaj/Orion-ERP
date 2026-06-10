// Copyright (c) 2026, Orion ERP and contributors

frappe.listview_settings["Salik or Darbs"] = {
	onload(listview) {
		const M = "orion_erp.orion_erp.doctype.salik_or_darbs.salik_or_darbs";

		listview.page.add_inner_button(__("Download Template"), () => {
			window.open(`/api/method/${M}.download_template`);
		});

		listview.page.add_inner_button(__("Import Salik Excel"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Import Salik / Tolls"),
				fields: [
					{ fieldname: "billing_month", label: __("Billing Month"), fieldtype: "Date", reqd: 1, default: frappe.datetime.month_start() },
					{ fieldname: "file", label: __("Excel Statement"), fieldtype: "Attach", reqd: 1 },
				],
				primary_action_label: __("Import"),
				primary_action(v) {
					frappe.call({
						method: `${M}.import_salik`,
						args: { file_url: v.file, billing_month: v.billing_month },
						freeze: true,
						freeze_message: __("Importing tolls…"),
						callback: (r) => {
							d.hide();
							if (r.message) {
								frappe.show_alert({
									message: __("{0} vehicles imported, {1} rows unmatched.", [r.message.vehicles, r.message.unmatched]),
									indicator: r.message.unmatched ? "orange" : "green",
								});
							}
							listview.refresh();
						},
					});
				},
			});
			d.show();
		});
	},
};
