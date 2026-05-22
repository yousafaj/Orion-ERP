// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Employee Certificate Notification Settings", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Employee Certificate Notification Settings", {
    setup: function (frm) {

        // Filter Role (only enabled roles)
        frm.set_query("role", "employee_certificate_notification_detail", function () {
            return {
                filters: {
                    disabled: 0
                }
            };
        });

        // Filter Sender (only email accounts with outgoing enabled)
        frm.set_query("sender", "employee_certificate_notification_detail", function () {
            return {
                filters: {
                    enable_outgoing: 1
                }
            };
        });

    }
});