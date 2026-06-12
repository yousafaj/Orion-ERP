// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salik or Darbs", {
	refresh(frm) {
		if (frm.doc.docstatus === 0 && !frm.is_new() && frm.doc.excel_attachment) {
			frm.add_custom_button(__("Parse & Match Excel"), () => {
				frappe.call({
					method: "orion_erp.orion_erp.doctype.salik_or_darbs.salik_or_darbs.parse_and_match",
					args: { name: frm.doc.name },
					freeze: true,
					freeze_message: __("Parsing statement…"),
					callback: (r) => {
						if (r.message) {
							frappe.show_alert({
								message: __("{0} charges parsed, {1} unmatched.", [
									r.message.total,
									r.message.unmatched,
								]),
								indicator: r.message.unmatched ? "orange" : "green",
							});
						}
						frm.reload_doc();
					},
				});
			}).addClass("btn-primary");
		}

		if (frm.doc.unmatched_count) {
			frm.dashboard.set_headline(
				__("{0} toll rows did not match a vehicle/rental — review the highlighted rows.", [
					frm.doc.unmatched_count,
				])
			);
		}
	},
});
