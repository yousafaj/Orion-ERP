# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AccidentLogs(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		incident_date: DF.Date | None
		incident_details: DF.SmallText | None
		location: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		project: DF.Link | None
		vrn: DF.Link | None
	# end: auto-generated types
	pass
