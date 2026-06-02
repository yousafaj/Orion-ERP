frappe.ui.form.on("Driver", {
    employee(frm) {
        if (!frm.doc.employee) return;

        frappe.call({
            method: "orion_erp.orion_erp.validations.driver_hooks.get_employee_certificates_for_driver",
            args: { employee: frm.doc.employee }
        }).then(r => {
            if (!r || r.exc) return;
            const rows = r.message || [];
            if (!rows.length) return;

            const do_copy = () => {
                frm.clear_table("custom_certification_list");
                rows.forEach(row => {
                    const newRow = frm.add_child("custom_certification_list");
                    newRow.certification_name = row.certification_name;
                    newRow.reference_no = row.reference_no;
                    newRow.date_of_issue = row.date_of_issue;
                    newRow.date_of_expiry = row.date_of_expiry;
                    newRow.attachment = row.attachment;
                });
                frm.refresh_field("custom_certification_list");
            };

            if ((frm.doc.custom_certification_list || []).length) {
                frappe.confirm(
                    __("Replace existing certificates with the {0} from this Employee?", [rows.length]),
                    do_copy
                );
            } else {
                do_copy();
            }
        });
    }
});