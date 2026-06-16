frappe.ui.form.on('Quotation', {
    custom_prepared_by: function(frm) {
        if (frm.doc.custom_prepared_by) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Employee',
                    filters: { name: frm.doc.custom_prepared_by },
                    fieldname: ['designation', 'custom_mobile', 'employee_name', 'user_id']
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('custom_designation', r.message.designation || '');
                        frm.set_value('custom_contact_no', r.message.custom_mobile || '');
                        frm.set_value('custom_contact_persons', r.message.employee_name || '');
                        frm.set_value('custom_email', r.message.user_id || '');
                    }
                }
            });
        } else {
            frm.set_value('custom_designation', '');
            frm.set_value('custom_contact_no', '');
            frm.set_value('custom_contact_persons', '');
            frm.set_value('custom_email', '');
        }
    }
});
