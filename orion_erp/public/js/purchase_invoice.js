frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {

        console.log("Purchase Invoice JS Loaded");
        update_recoverable_expenses(frm);
    },

    taxes_add(frm) {
        update_recoverable_expenses(frm);
    },

    taxes_remove(frm) {
        update_recoverable_expenses(frm);
    },

    validate(frm) {
        update_recoverable_expenses(frm);
    }
});

frappe.ui.form.on("Purchase Taxes and Charges", {
    tax_amount(frm, cdt, cdn) {
        update_recoverable_expenses(frm);
    },

    rate(frm, cdt, cdn) {
        update_recoverable_expenses(frm);
    },

    account_head(frm, cdt, cdn) {
        update_recoverable_expenses(frm);
    }
});

function update_recoverable_expenses(frm) {
    let amount = flt(frm.doc.total_taxes_and_charges);

    frm.set_value("recoverable_standard_rated_expenses", amount);
}