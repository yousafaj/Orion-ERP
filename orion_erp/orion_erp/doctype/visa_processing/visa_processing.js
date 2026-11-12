frappe.ui.form.on("Visa Processing", {
	refresh: function(frm) {


        if (frm.doc.change_status_approval === "Approved" && frm.doc.staff_category === "Non Office Staff" && !frm.is_new()) {

            frm.add_custom_button(__('Send to Operations'), function() {
                frappe.confirm(__('Send the details and driving license copy to the Operations department?'), function() {
                    frappe.call({
                        method: 'orion_erp.orion_erp.doctype.visa_processing.visa_processing.send_to_operations',
                        args: { docname: frm.doc.name },
                        freeze: true,
                        freeze_message: __('Sending...'),
                        callback: function(r) {
                            if (r.message === 'sent') {
                                frappe.show_alert({message: __('Sent to Operations'), indicator: 'green'});
                                frm.reload_doc();
                            }
                        }
                    });
                });
            }, __('Actions'));
        }

        

        // Show button only when status is Approved
        // if (frm.doc.status === "Approved" && !frm.is_new()) {

        if (
            frm.doc.status === "Approved" ||
            frm.doc.change_status_approval === "Approved" &&
            !frm.is_new()
        ) {


            frm.add_custom_button(__('Create Employee'), function() {

                frappe.model.with_doctype('Employee', function() {

                    // Create new Employee document
                    let employee = frappe.model.get_new_doc('Employee');

                    // Fetch candidate name
                    employee.first_name = frm.doc.candidate_name;

                    // Fields that must not be copied from a child row
                    const skip_fields = [
                        'name',
                        'parent',
                        'parentfield',
                        'parenttype',
                        'doctype',
                        'idx',
                        'owner',
                        'creation',
                        'modified',
                        'modified_by',
                        'docstatus'
                    ];

                    // Copy Certificates child table
                    (frm.doc.certificates || []).forEach(source_row => {

                        let child = frappe.model.add_child(
                            employee,
                            'Employee cdt',
                            'custom_certificates'
                        );

                        // Copy all certificate fields
                        Object.keys(source_row).forEach(field => {

                            if (!skip_fields.includes(field)) {
                                child[field] = source_row[field];
                            }
                        });

                    });

                    // Copy Job Offer Terms child table
                    // Visa Processing: custom_job_offer_terms -> Employee: custom_job_offer_terms
                    (frm.doc.custom_job_offer_terms || frm.doc.job_offer_terms || []).forEach(source_row => {

                        let child = frappe.model.add_child(
                            employee,
                            'Job Offer Term',
                            'custom_job_offer_terms'
                        );

                        Object.keys(source_row).forEach(field => {

                            if (!skip_fields.includes(field)) {
                                child[field] = source_row[field];
                            }
                        });

                    });

                    // Open Employee form
                    frappe.set_route(
                        'Form',
                        'Employee',
                        employee.name
                    );

                });

            }, __('Actions'));

        }
    }

});


