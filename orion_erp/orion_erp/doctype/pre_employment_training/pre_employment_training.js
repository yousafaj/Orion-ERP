// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pre-Employment Training", {
	refresh(frm) {

    if (frm.doc.status === "Completed" && !frm.doc.sent_to_hr && !frm.is_new()) {

    frm.add_custom_button(__('Send to HR'), function() {
        frappe.confirm(__('Send the training completion details to all HR users?'), function() {
            frappe.call({
                method: 'orion_erp.orion_erp.doctype.pre_employment_training.pre_employment_training.send_to_hr',
                args: { docname: frm.doc.name },
                freeze: true,
                freeze_message: __('Sending...'),
                callback: function(r) {
                    if (r.message === 'sent') {
                        frappe.show_alert({message: __('Sent to HR'), indicator: 'green'});
                        frm.reload_doc();
                    }
                }
            });
        });
    }, __('Actions'));
}

	},
});
