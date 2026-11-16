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


job_applicant(frm) {
        // ---- change these names if yours are different (see note below) ----
        const VISA_DOCTYPE      = 'Visa Processing';
        const VISA_LINK_FIELD   = 'job_applicant';   // field in Visa Processing that links to Job Applicant
        const VISA_CHILD_TABLE  = 'certificates';    // Certificates table in Visa Processing
        const TARGET_TABLE      = 'documents';       // Documents table in Pre-Employment Training

        // Visa Processing certificate field  ->  Pre-Employment Training document field
        const MAP = {
            certification_name: 'name1',   // Certification Name -> Name
            date_of_issue:      'issued_date',     // Date of Issue      -> Issued Date
            date_of_expiry:     'expiry_date' ,     // Date of Expiry  
            attachment :         'attachment'
        };
        // ---------------------------------------------------------------------

        frm.clear_table(TARGET_TABLE);
        frm.refresh_field(TARGET_TABLE);
        if (!frm.doc.job_applicant) return;

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: VISA_DOCTYPE,
                filters: { [VISA_LINK_FIELD]: frm.doc.job_applicant },
                fields: ['name'],
                order_by: 'modified desc',
                limit_page_length: 1
            },
            callback(r) {
                if (!r.message || !r.message.length) {
                    frappe.show_alert({ message: __('No Visa Processing record found for this applicant'), indicator: 'orange' });
                    return;
                }
                frappe.call({
                    method: 'frappe.client.get',
                    args: { doctype: VISA_DOCTYPE, name: r.message[0].name },
                    callback(res) {
                        const rows = (res.message && res.message[VISA_CHILD_TABLE]) || [];
                        rows.forEach(src => {
                            const row = frm.add_child(TARGET_TABLE);
                            Object.keys(MAP).forEach(k => { row[MAP[k]] = src[k]; });
                        });
                        frm.refresh_field(TARGET_TABLE);
                        frappe.show_alert({ message: __('{0} certificate(s) fetched', [rows.length]), indicator: 'green' });
                    }
                });
            }
        });
    }

});


// frappe.ui.form.on('Pre-Employment Training', {
    