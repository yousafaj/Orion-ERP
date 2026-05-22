// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("CICPA", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.cicpa_status === "Active") {
			const add_mark_button = (label, new_status) => {
				frm.add_custom_button(__(label), function () {
					frappe.confirm(
						__("Mark this CICPA as {0}? This cannot be undone.", [__(new_status)]),
						function () {
							frappe.call({
								method: "rental_management.rental_management.doctype.cicpa.cicpa.mark_cicpa_status",
								args: { cicpa: frm.doc.name, new_status: new_status },
								freeze: true,
								callback: function (r) {
									if (!r.exc) {
										frm.reload_doc();
									}
								}
							});
						}
					);
				}, __("Actions"));
			};

			add_mark_button("Mark as Cancelled", "Cancelled");
			add_mark_button("Mark as Lost", "Lost");
			add_mark_button("Mark as Expired", "Expired");
		}
	},

	after_cancel(frm) {
		frappe.confirm(
			"Are you sure you want to cancel this CICPA and delete all linked CICPA Logs?",
			function () {
				// Proceed with cancellation
				frappe.call({
					method: "frappe.client.get_list",
					args: {
						doctype: "CICPA Logs",
						filters: {
							cicpa: frm.doc.name
						},
						fields: ["name"]
					},
					callback: function (r) {
						if (r.message) {
							r.message.forEach(log => {
								frappe.call({
									method: "frappe.client.delete",
									args: {
										doctype: "CICPA Logs",
										name: log.name
									},
									callback: function () {
										console.log("Deleted log:", log.name);
									}
								});
							});
						}
					}
				});
				// let cancel continue
				frm.script_manager.trigger("cancel");
			},
			function () {
				// If user cancels confirmation dialog, prevent cancel
				frappe.msgprint("Cancellation aborted.");
			}
		);

		// Prevent default cancel until user confirms
		return false;
	}
});
