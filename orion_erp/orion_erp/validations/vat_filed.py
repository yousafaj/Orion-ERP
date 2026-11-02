import frappe
from frappe import _


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