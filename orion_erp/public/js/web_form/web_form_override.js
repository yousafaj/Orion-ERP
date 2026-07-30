frappe.ready(function () {
    var wf = frappe.web_form;
    if (!wf || !wf.fields_list) return;

    wf.fields_list.forEach(function (field) {
        if (field.df.fieldtype !== "Table MultiSelect") return;

        if (!field.df.get_data) {
            field.df.get_data = function () {
                var doc = frappe.web_form_doc;
                if (doc && doc[field.df.fieldname]) {
                    return doc[field.df.fieldname];
                }
                return [];
            };
        }
    });
});
