frappe.ui.form.on("Salary Detail", {
    form_render(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (
            row.salary_component === "House Rent Allowance" &&
            row.custom_print_hide == null
        ) {
            frappe.model.set_value(
                cdt,
                cdn,
                "custom_print_hide",
                1
            );
        }
    }
});