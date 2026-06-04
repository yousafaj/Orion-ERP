// Copyright (c) 2026, Orion ERP and contributors

frappe.listview_settings["Traffic Fine or Accident"] = {
	onload(listview) {
		const M = "orion_erp.orion_erp.doctype.traffic_fine_or_accident.traffic_fine_or_accident";

		listview.page.add_inner_button(__("Download Template"), () => {
			window.open(`/api/method/${M}.download_template`);
		});

		listview.page.add_inner_button(__("Import Fines Excel"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Import Fines"),
				fields: [{ fieldname: "file", label: __("Excel"), fieldtype: "Attach", reqd: 1 }],
				primary_action_label: __("Import"),
				primary_action(v) {
					frappe.call({
						method: `${M}.import_fines`,
						args: { file_url: v.file },
						freeze: true,
						freeze_message: __("Importing fines…"),
						callback: (r) => {
							d.hide();
							if (r.message) {
								frappe.show_alert({
									message: __("{0} fines created, {1} rows unmatched.", [r.message.created, r.message.unmatched]),
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
