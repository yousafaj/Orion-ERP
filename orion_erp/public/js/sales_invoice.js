const EXC = "custom_exclude_from_vat_report";

frappe.ui.form.on("Sales Invoice", {
    taxes_and_charges(frm) { orion_set_exclude(frm); },
    before_save(frm) { return orion_set_exclude(frm); },
});

frappe.ui.form.on("Sales Invoice Item", {
    item_tax_template(frm) { orion_set_exclude(frm); },
    items_remove(frm) { orion_set_exclude(frm); },
});

async function orion_set_exclude(frm) {
    if (frm.doc.docstatus !== 0) return;

    const names = [...new Set((frm.doc.items || [])
        .map(r => r.item_tax_template).filter(Boolean))];
    let flags = {};
    if (names.length) {
        const list = await frappe.db.get_list("Item Tax Template", {
            filters: { name: ["in", names] },
            fields: ["name", EXC],
            limit: 0,
        });
        list.forEach(t => (flags[t.name] = cint(t[EXC])));
    }

    (frm.doc.items || []).forEach(r => {
        const f = r.item_tax_template ? cint(flags[r.item_tax_template]) : 0;
        if (cint(r[EXC]) !== f) frappe.model.set_value(r.doctype, r.name, EXC, f);
    });

    let tpl = 0;
    if (frm.doc.taxes_and_charges) {
        const v = await frappe.db.get_value(
            "Sales Taxes and Charges Template", frm.doc.taxes_and_charges, EXC);
        tpl = cint((v.message || {})[EXC]);
    }

    const any_item = Object.values(flags).some(f => f === 1);
    const header = (tpl || any_item) ? 1 : 0;

    if (cint(frm.doc[EXC]) !== header) await frm.set_value(EXC, header);
}