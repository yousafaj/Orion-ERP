frappe.ui.form.on("Salary Slip", {
    refresh(frm) {
        ["earnings", "deductions"].forEach(field => {
            let grid = frm.fields_dict[field]?.grid;
            if (!grid) return;
            grid.cannot_add_rows = true;
            grid.cannot_delete_rows = true;
            setTimeout(() => {
                grid.wrapper.find('.grid-remove-rows').hide();
                grid.wrapper.find('.grid-checkbox').hide();
            }, 100);
        });
    }
});

frappe.ui.form.on("Salary Detail", {
    amount(frm, cdt, cdn) {
        setTimeout(() => {
            let gross_pay = 0;
            let total_deduction = 0;

            (frm.doc.earnings || []).forEach(row => {
                if (!row.do_not_include_in_total) {
                    gross_pay += flt(row.amount);
                }
            });

            (frm.doc.deductions || []).forEach(row => {
                if (!row.do_not_include_in_total) {
                    total_deduction += flt(row.amount);
                }
            });

            frm.set_value("gross_pay", gross_pay);
            frm.set_value("total_deduction", total_deduction);

            let net_pay = gross_pay - total_deduction - flt(frm.doc.total_loan_repayment);
            frm.set_value("net_pay", net_pay);
            frm.set_value("rounded_total", Math.round(net_pay));
        }, 300);
    },
    form_render(frm, cdt, cdn) {
        setTimeout(() => {
            $('.grid-delete-row').hide();
            $('.grid-insert-row-below').hide();
            $('.grid-insert-row').hide();
        }, 100);

        let row = locals[cdt][cdn];
        if (
            row.salary_component === "Rent Allowances" &&
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