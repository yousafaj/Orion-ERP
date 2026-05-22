# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class MaintenanceScheduling(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		activity_type: DF.Literal["", "Engine", "Body", "Suspension"]
		incident_details: DF.SmallText | None
		odometer_reading_in: DF.Float
		odometer_reading_out: DF.Float
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		replacement_part: DF.Data | None
	# end: auto-generated types
	pass
