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
    }
});