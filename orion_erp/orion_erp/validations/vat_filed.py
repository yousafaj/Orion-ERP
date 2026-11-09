import frappe
from frappe import _
from frappe.utils import cint


def block_cancel_if_vat_filed(doc, method=None):
	"""Sales Invoice / Purchase Invoice already included in a VAT return
	(custom_vat_filed ticked) cannot be cancelled."""
	if doc.get("custom_vat_filed"):
		frappe.throw(
			_("{0} {1} is already included in a filed VAT return, so it cannot be cancelled.").format(
				_(doc.doctype), doc.name
			),
			title=_("Cannot cancel"),
		)



FIELD = "custom_exclude_from_vat_report"


def set_vat_exclude_flag(doc, method=None):
    templates = {r.item_tax_template for r in doc.items if r.item_tax_template}
    flags = {}
    if templates:
        flags = {
            t.name: cint(t.get(FIELD))
            for t in frappe.get_all(
                "Item Tax Template",
                filters={"name": ["in", list(templates)]},
                fields=["name", FIELD],
            )
        }
    for r in doc.items:
        r.set(FIELD, cint(flags.get(r.item_tax_template)) if r.item_tax_template else 0)

    tpl = 0
    if doc.taxes_and_charges:
        tpl = cint(frappe.db.get_value(
            "Sales Taxes and Charges Template", doc.taxes_and_charges, FIELD))

    any_item = any(cint(r.get(FIELD)) for r in doc.items)
    doc.set(FIELD, 1 if (tpl or any_item) else 0)



def set_purchase_exclude_flags(doc, method=None):
    templates = {r.item_tax_template for r in doc.items if r.item_tax_template}
    if not templates or not doc.taxes:
        return

    accounts = set()
    for name in templates:
        tpl = frappe.get_doc("Item Tax Template", name)
        if cint(tpl.get("custom_exclude_from_vat_report")):
            for t in tpl.taxes:
                if not cint(t.get("not_applicable")) and t.tax_type:
                    accounts.add(t.tax_type)

    for row in doc.taxes:
        if row.account_head in accounts:
            row.set("custom_exclude_from_recoverable_vat", 1)