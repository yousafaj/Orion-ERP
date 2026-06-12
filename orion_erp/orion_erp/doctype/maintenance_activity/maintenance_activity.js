// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Maintenance Activity", {
	refresh(frm) {
		frm.dashboard.clear_comment();
		frm.dashboard.add_comment(
			__("Vehicle Maintenance is disabled. Track workshop time with 'To Workshop' on the Vehicle Movement."),
			"yellow",
			true
		);
		if (frm.is_new()) frm.disable_save();
	},
});
