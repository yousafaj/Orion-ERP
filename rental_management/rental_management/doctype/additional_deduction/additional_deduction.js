// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Additional Deduction", {
	setup(frm) {
        frm.fields_dict.salary_component.get_query = function() {
            return {
                filters: {
                    type: "Deduction"
                }
            };
        };
    },
});
