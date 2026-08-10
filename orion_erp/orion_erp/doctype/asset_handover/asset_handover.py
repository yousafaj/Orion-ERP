# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AssetHandover(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from orion_erp.orion_erp.doctype.asset_handover_detail.asset_handover_detail import AssetHandoverDetail

		asset_handover_detail: DF.Table[AssetHandoverDetail]
		department: DF.Link | None
		designation: DF.Link | None
		employee: DF.Link | None
		employee_name: DF.Data | None
		naming_series: DF.Literal[None]
		remarks: DF.Text | None
	# end: auto-generated types

	def validate(self):
		self.validate_one_handover_per_employee()

	def validate_one_handover_per_employee(self):
		if not self.employee:
			return

		existing = frappe.db.exists(
			"Asset Handover",
			{
				"employee": self.employee,
				"name": ["!=", self.name],
			},
		)
		if existing:
			frappe.throw(
				f"Asset Handover <b>{existing}</b> already exists for employee <b>{self.employee}</b>. "
				"Only one Asset Handover is allowed per employee."
			)
