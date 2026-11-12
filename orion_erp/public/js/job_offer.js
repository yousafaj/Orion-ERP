frappe.ui.form.on("Job Offer", {
    job_offer_term_template(frm) {

        if (!frm.doc.job_offer_term_template) {
            return;
        }

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Job Offer Term Template",
                name: frm.doc.job_offer_term_template
            },
            callback: function(r) {

                if (r.message) {

                    // clear existing rows only when template changes
                    frm.clear_table("offer_terms");

                    (r.message.offer_terms || []).forEach(term => {

                        let row = frm.add_child("offer_terms");

                        row.offer_term = term.offer_term;
                        row.value = term.value;
                    });

                    frm.refresh_field("offer_terms");
                }
            }
        });
    },

    // refresh: function(frm) {

    //     if (frm.doc.workflow_state === "Approved") {

    //         frm.add_custom_button(__('Visa Processing'), function() {

    //             frappe.new_doc('Visa Processing', {
    //                 job_applicant: frm.doc.job_applicant,
    //                 candidate_name: frm.doc.applicant_name

    //             });

    //         }, __('Actions'));

    //     }
    // }

    // refresh: function(frm) {

    //     if (frm.doc.workflow_state === "Approved") {

    //         frm.add_custom_button(__('Visa Processing'), function() {

    //             frappe.model.with_doctype('Visa Processing', function() {

    //                 // Create new Visa Processing document
    //                 let doc = frappe.model.get_new_doc('Visa Processing');

    //                 // Fetch Job Offer details
    //                 doc.job_applicant = frm.doc.job_applicant;
    //                 doc.candidate_name = frm.doc.applicant_name;

    //                 // Copy Certificates child table
    //                 (frm.doc.custom_certificates || []).forEach(source_row => {

    //                     let child = frappe.model.add_child(
    //                         doc,
    //                         'certificates'
    //                     );

    //                     // Copy all certificate fields
    //                     Object.keys(source_row).forEach(field => {

    //                         if (![
    //                             'name',
    //                             'parent',
    //                             'parentfield',
    //                             'parenttype',
    //                             'doctype',
    //                             'idx',
    //                             'owner',
    //                             'creation',
    //                             'modified',
    //                             'modified_by',
    //                             'docstatus'
    //                         ].includes(field)) {

    //                             child[field] = source_row[field];
    //                         }
    //                     });

    //                 });

    //                 // Open new Visa Processing document
    //                 frappe.set_route(
    //                     'Form',
    //                     'Visa Processing',
    //                     doc.name
    //                 );

    //             });

    //         }, __('Actions'));

    //     }
    // }

    refresh: function(frm) {

        const hide_for = [
            "elizabeth@oriongroup.ae",
            "jayshree@oriongroup.ae"
        ];

        // Hide only for these two users, and only after the record is saved
        const hide = !frm.is_new() && hide_for.includes(frappe.session.user);

        frm.set_df_property("offer_terms", "hidden", hide ? 1 : 0);
        frm.set_df_property("custom_additional_allowance", "hidden", hide ? 1 : 0);


    if (frm.doc.workflow_state === "Approved") {

        frm.add_custom_button(__('Visa Processing'), function() {

            frappe.model.with_doctype('Visa Processing', function() {

                // Create new Visa Processing document
                let doc = frappe.model.get_new_doc('Visa Processing');

                // Fetch Job Offer details
                doc.job_applicant = frm.doc.job_applicant;
                doc.candidate_name = frm.doc.applicant_name;

                // Fields that must not be copied from a child row
                const skip_fields = [
                    'name', 'parent', 'parentfield', 'parenttype',
                    'doctype', 'idx', 'owner', 'creation',
                    'modified', 'modified_by', 'docstatus'
                ];

                // Helper: copy all rows from a source table to a target table
                function copy_table(source_rows, target_fieldname) {
                    (source_rows || []).forEach(source_row => {
                        let child = frappe.model.add_child(doc, target_fieldname);

                        Object.keys(source_row).forEach(field => {
                            if (!skip_fields.includes(field)) {
                                child[field] = source_row[field];
                            }
                        });
                    });
                }

                // Copy Certificates table
                copy_table(frm.doc.custom_certificates, 'certificates');

                // Copy Job Offer Terms table
                // Job Offer: offer_terms  ->  Visa Processing: job_offer_terms
                copy_table(frm.doc.offer_terms, 'job_offer_terms');

                // Open new Visa Processing document
                frappe.set_route('Form', 'Visa Processing', doc.name);

            });

        }, __('Actions'));
    }
}




});
