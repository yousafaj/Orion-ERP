frappe.ui.form.on("Workshop Request", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.status === "Approved" && !frm.doc.job_card) {
            frm.add_custom_button(__("Create Job Card"), () => {
                frappe.call({
                    method: "orion_erp.workshop.doctype.workshop_request.workshop_request.make_job_card",
                    args: { request_name: frm.doc.name },
                    freeze: true,
                    callback(r) {
                        if (r.message) {
                            frappe.set_route("Form", "Workshop Job Card", r.message);
                        }
                    },
                });
            });
        }
    },
});
