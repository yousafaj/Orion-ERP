# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PenaltiesDetails(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		date_of_deduction_occurred: DF.Date | None
		employee_deduction_reference: DF.Data | None
		installation_amount: DF.Currency
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		penalty_name: DF.Link | None
		remaining_amount: DF.Currency
		remarks: DF.Text | None
	# end: auto-generated types
	pass
