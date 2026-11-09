



// const RSRE = "recoverable_standard_rated_expenses";
// const EXCLUDE_FIELD = "custom_exclude_from_recoverable_vat";

// frappe.ui.form.on("Purchase Invoice", {
//     onload(frm) {
//         orion_wrap_calc(frm);
//     },

//     refresh(frm) {
//         orion_wrap_calc(frm);
//         orion_sync_later(frm);
//     },

//     // Template selected: copy the template's tick to the loaded rows, then recalc
//     taxes_and_charges(frm) {
//         orion_apply_template_flag(frm);
//     },

//     taxes_add(frm) {
//         orion_sync_later(frm);
//     },

//     taxes_remove(frm) {
//         orion_sync_later(frm);
//     },

//     items_add(frm) {
//         orion_sync_later(frm);
//     },

//     items_remove(frm) {
//         orion_sync_later(frm);
//     },

//     reverse_charge(frm) {
//         if (frm.doc.reverse_charge === "Y") {
//             frm.set_value(RSRE, 0);
//         } else {
//             orion_sync_later(frm);
//         }
//     },

//     // Make sure the saved value is always correct
//     before_save(frm) {
//         const value = orion_compute(frm);
//         if (value !== null) {
//             frm.doc[RSRE] = value;
//         }
//     },
// });

// frappe.ui.form.on("Purchase Invoice Item", {
//     qty(frm) { orion_sync_later(frm); },
//     rate(frm) { orion_sync_later(frm); },
//     item_code(frm) { orion_sync_later(frm); },
//     item_tax_template(frm) { orion_sync_later(frm); }   // item-wise tax
// });

// frappe.ui.form.on("Purchase Taxes and Charges", {
//     custom_exclude_from_recoverable_vat(frm) {
//         orion_apply(frm);                                // tick/untick -> instant
//     },
//     account_head(frm) { orion_sync_later(frm); },
//     charge_type(frm) { orion_sync_later(frm); },
//     rate(frm) { orion_sync_later(frm); },
//     tax_amount(frm) { orion_sync_later(frm); },
//     add_deduct_tax(frm) { orion_sync_later(frm); }
// });


// // Hook into ERPNext's tax calculation (runs for template, item-wise tax, direct rows)
// function orion_wrap_calc(frm) {
//     if (frm._orion_wrapped) return;
//     if (!frm.cscript || typeof frm.cscript.calculate_taxes_and_totals !== "function") return;

//     const original = frm.cscript.calculate_taxes_and_totals;

//     frm.cscript.calculate_taxes_and_totals = function () {
//         const result = original.apply(this, arguments);

//         if (result && typeof result.then === "function") {
//             result.then(() => orion_apply(frm));
//         } else {
//             orion_apply(frm);
//         }
//         orion_sync_later(frm);   // safety net, debounced
//         return result;
//     };

//     frm._orion_wrapped = true;
// }


// // Debounced re-run so many quick events cause only one recalculation
// function orion_sync_later(frm) {
//     clearTimeout(frm._orion_timer);
//     frm._orion_timer = setTimeout(() => orion_apply(frm), 500);
// }


// // Returns the recoverable amount, or null if it should not be touched
// function orion_compute(frm) {
//     if (frm.doc.docstatus !== 0) return null;
//     if (frm.doc.custom_vat_filed) return null;
//     if (frm.doc.reverse_charge === "Y") return 0;

//     let recoverable = 0;

//     (frm.doc.taxes || []).forEach(row => {

//         // Ticked rows are excluded
//         if (cint(row[EXCLUDE_FIELD]) === 1) return;

//         // Uses the final per-row amount. With item-wise tax this is already
//         // the sum of each item's tax for that row.
//         let amount = flt(row.base_tax_amount_after_discount_amount)
//             || flt(row.base_tax_amount)
//             || flt(row.tax_amount);

//         if (row.add_deduct_tax === "Deduct") {
//             amount = -Math.abs(amount);
//         }

//         recoverable += amount;
//     });

//     return flt(recoverable, 2);
// }


// function orion_apply(frm) {
//     const recoverable = orion_compute(frm);
//     if (recoverable === null) return;

//     if (flt(frm.doc[RSRE], 2) !== recoverable) {
//         frm.set_value(RSRE, recoverable);
//     }
// }


// // Copy the template's "Exclude from Recoverable VAT" tick to rows loaded from it
// function orion_apply_template_flag(frm) {

//     const template = frm.doc.taxes_and_charges;
//     if (!template) {
//         orion_sync_later(frm);
//         return;
//     }

//     const before = (frm.doc.taxes || []).map(r => r.name).join(",");

//     frappe.db.get_doc("Purchase Taxes and Charges Template", template).then(tpl => {

//         // template row flags by position
//         const flags = {};
//         (tpl.taxes || []).forEach(t => {
//             flags[t.idx] = cint(t[EXCLUDE_FIELD]);
//         });

//         let tries = 0;
//         const timer = setInterval(() => {
//             tries++;

//             const now = (frm.doc.taxes || []).map(x => x.name).join(",");
//             const loaded = now && now !== before;

//             if (loaded || tries >= 12) {
//                 clearInterval(timer);

//                 (frm.doc.taxes || []).forEach(row => {
//                     const flag = cint(flags[row.idx]);
//                     if (cint(row[EXCLUDE_FIELD]) !== flag) {
//                         frappe.model.set_value(row.doctype, row.name, EXCLUDE_FIELD, flag);
//                     }
//                 });

//                 orion_apply(frm);
//             }
//         }, 400);
//     });
// }



const RSRE = "recoverable_standard_rated_expenses";
const EXCLUDE_FIELD = "custom_exclude_from_recoverable_vat";   // on Purchase Taxes and Charges rows
const ITEM_TPL_FLAG = "custom_exclude_from_vat_report";         // on Item Tax Template

frappe.ui.form.on("Purchase Invoice", {
    onload(frm) {
        orion_wrap_calc(frm);
    },

    refresh(frm) {
        orion_wrap_calc(frm);
        orion_sync_later(frm);
    },

    // Purchase Taxes and Charges Template selected
    taxes_and_charges(frm) {
        orion_apply_template_flag(frm);
    },

    taxes_add(frm) { orion_sync_later(frm); },
    taxes_remove(frm) { orion_sync_later(frm); },
    items_add(frm) { orion_sync_later(frm); },
    items_remove(frm) { orion_sync_later(frm); },

    reverse_charge(frm) {
        if (frm.doc.reverse_charge === "Y") {
            frm.set_value(RSRE, 0);
        } else {
            orion_sync_later(frm);
        }
    },

    // Make sure ticks and the saved value are always right
    async before_save(frm) {
        await orion_tick_item_wise(frm);
        const value = orion_compute(frm);
        if (value !== null) {
            frm.doc[RSRE] = value;
        }
    },
});

frappe.ui.form.on("Purchase Invoice Item", {
    qty(frm) { orion_sync_later(frm); },
    rate(frm) { orion_sync_later(frm); },
    item_code(frm) { orion_sync_later(frm); },
    item_tax_template(frm) { orion_sync_later(frm); },   // item-wise tax
});

frappe.ui.form.on("Purchase Taxes and Charges", {
    custom_exclude_from_recoverable_vat(frm) {
        orion_apply(frm);                                 // tick/untick -> instant
    },
    account_head(frm) { orion_sync_later(frm); },
    charge_type(frm) { orion_sync_later(frm); },
    rate(frm) { orion_sync_later(frm); },
    tax_amount(frm) { orion_sync_later(frm); },
    add_deduct_tax(frm) { orion_sync_later(frm); },
});


// Hook into ERPNext's tax calculation (runs for template, item-wise tax, direct rows)
function orion_wrap_calc(frm) {
    if (frm._orion_wrapped) return;
    if (!frm.cscript || typeof frm.cscript.calculate_taxes_and_totals !== "function") return;

    const original = frm.cscript.calculate_taxes_and_totals;

    frm.cscript.calculate_taxes_and_totals = function () {
        const result = original.apply(this, arguments);

        if (result && typeof result.then === "function") {
            result.then(() => orion_apply(frm));
        } else {
            orion_apply(frm);
        }
        orion_sync_later(frm);
        return result;
    };

    frm._orion_wrapped = true;
}


// Debounced: item-wise ticks first, then the recoverable amount
function orion_sync_later(frm) {
    clearTimeout(frm._orion_timer);
    frm._orion_timer = setTimeout(async () => {
        await orion_tick_item_wise(frm);
        orion_apply(frm);
    }, 500);
}


// Item-wise tax: tick rows covered by an Item Tax Template that has
// "Exclude from VAT Report" ticked. Only ever ticks; it never unticks a row.
async function orion_tick_item_wise(frm) {
    if (frm.doc.docstatus !== 0) return;
    if (!(frm.doc.taxes || []).length) return;

    const names = [...new Set((frm.doc.items || [])
        .map(r => r.item_tax_template).filter(Boolean))];
    if (!names.length) return;

    const accounts = new Set();
    for (const name of names) {
        const tpl = await frappe.db.get_doc("Item Tax Template", name);
        if (!cint(tpl[ITEM_TPL_FLAG])) continue;
        (tpl.taxes || []).forEach(t => {
            if (!cint(t.not_applicable) && t.tax_type) accounts.add(t.tax_type);
        });
    }
    if (!accounts.size) return;

    (frm.doc.taxes || []).forEach(row => {
        if (accounts.has(row.account_head) && !cint(row[EXCLUDE_FIELD])) {
            frappe.model.set_value(row.doctype, row.name, EXCLUDE_FIELD, 1);
        }
    });
}


// Returns the recoverable amount, or null if it should not be touched
function orion_compute(frm) {
    if (frm.doc.docstatus !== 0) return null;
    if (frm.doc.custom_vat_filed) return null;
    if (frm.doc.reverse_charge === "Y") return 0;

    let recoverable = 0;

    (frm.doc.taxes || []).forEach(row => {
        // Ticked rows are excluded
        if (cint(row[EXCLUDE_FIELD]) === 1) return;

        let amount = flt(row.base_tax_amount_after_discount_amount)
            || flt(row.base_tax_amount)
            || flt(row.tax_amount);

        if (row.add_deduct_tax === "Deduct") {
            amount = -Math.abs(amount);
        }
        recoverable += amount;
    });

    return flt(recoverable, 2);
}


function orion_apply(frm) {
    const recoverable = orion_compute(frm);
    if (recoverable === null) return;

    if (flt(frm.doc[RSRE], 2) !== recoverable) {
        frm.set_value(RSRE, recoverable);
    }
}


// Copy the template's row ticks to the rows loaded from it, then add item-wise ticks
function orion_apply_template_flag(frm) {

    const template = frm.doc.taxes_and_charges;
    if (!template) {
        orion_sync_later(frm);
        return;
    }

    const before = (frm.doc.taxes || []).map(r => r.name).join(",");

    frappe.db.get_doc("Purchase Taxes and Charges Template", template).then(tpl => {

        const flags = {};
        (tpl.taxes || []).forEach(t => {
            flags[t.idx] = cint(t[EXCLUDE_FIELD]);
        });

        let tries = 0;
        const timer = setInterval(() => {
            tries++;

            const now = (frm.doc.taxes || []).map(x => x.name).join(",");
            const loaded = now && now !== before;

            if (loaded || tries >= 12) {
                clearInterval(timer);

                (frm.doc.taxes || []).forEach(row => {
                    const flag = cint(flags[row.idx]);
                    if (cint(row[EXCLUDE_FIELD]) !== flag) {
                        frappe.model.set_value(row.doctype, row.name, EXCLUDE_FIELD, flag);
                    }
                });

                orion_sync_later(frm);   // adds item-wise ticks, then recalculates
            }
        }, 400);
    });
}