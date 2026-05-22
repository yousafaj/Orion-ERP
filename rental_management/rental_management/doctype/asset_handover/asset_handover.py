# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AssetHandover(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.asset_handover_detail.asset_handover_detail import AssetHandoverDetail

		asset_handover_detail: DF.Table[AssetHandoverDetail]
		department: DF.Link | None
		designation: DF.Link | None
		employee: DF.Link | None
		employee_name: DF.Data | None
		naming_series: DF.Literal[None]
		remarks: DF.Text | None
	# end: auto-generated types
	pass
