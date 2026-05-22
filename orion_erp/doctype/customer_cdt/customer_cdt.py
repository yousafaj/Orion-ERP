# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Customercdt(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attachment: DF.Attach | None
		certification_name: DF.Link
		date_of_expiry: DF.Date
		date_of_issue: DF.Date
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reference_no: DF.Data
	# end: auto-generated types
	pass
