# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Drivershiftscdt(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		driver: DF.Link | None
		mobilization: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		shift: DF.Link | None
	# end: auto-generated types
	pass
