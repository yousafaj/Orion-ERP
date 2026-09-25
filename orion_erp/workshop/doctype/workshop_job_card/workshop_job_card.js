frappe.ui.form.on("Workshop Job Card", {
    vehicle(frm) {
        if (!frm.doc.vehicle) {
            return;
        }
        frappe.db.get_value("Vehicle", frm.doc.vehicle, ["custom_asset_mapping", "custom_company"]).then((r) => {
            const values = r.message || {};
            if (!frm.doc.asset && values.custom_asset_mapping) {
                frm.set_value("asset", values.custom_asset_mapping);
            }
            if (!frm.doc.company && values.custom_company) {
                frm.set_value("company", values.custom_company);
            }
        });
    },
});

frappe.ui.form.on("Workshop Job Part", {
    qty: calculate_part_amount,
    rate: calculate_part_amount,
});

function calculate_part_amount(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
}
