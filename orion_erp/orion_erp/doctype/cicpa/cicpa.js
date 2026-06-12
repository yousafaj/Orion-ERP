// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("CICPA", {
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
