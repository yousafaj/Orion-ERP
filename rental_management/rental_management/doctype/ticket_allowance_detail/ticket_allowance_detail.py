# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TicketAllowanceDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		from_date: DF.Date | None
		manual_paid: DF.Check
		outstanding_amount: DF.Currency
		paid: DF.Check
		paid_amount: DF.Currency
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		partial_paid: DF.Check
		references_data: DF.LongText | None
		to_date: DF.Date | None
	# end: auto-generated types
	pass
