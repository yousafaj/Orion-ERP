# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SalikorDarbs(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from orion_erp.orion_erp.doctype.fines_cdt.fines_cdt import Finescdt

		amended_from: DF.Link | None
		customer: DF.Link | None
		date: DF.Date
		detail: DF.Table[Finescdt]
		driver: DF.Link | None
		employment_type: DF.Link | None
		post_salik: DF.Check
		project: DF.Link | None
		shift: DF.Link | None
		type: DF.Literal["", "With Driver", "Without Driver"]
		vehicle: DF.Link | None
		vehicle_type: DF.Data | None
	# end: auto-generated types
	pass
