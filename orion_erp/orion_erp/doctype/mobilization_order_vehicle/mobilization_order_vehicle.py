# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class MobilizationOrderVehicle(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		deployment: DF.Link | None
		driver: DF.Link | None
		driver_name: DF.Data | None
		mobilization_date: DF.Date | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		status: DF.Literal["Pending", "Mobilized", "Demobilized"]
		sub_location: DF.Data | None
		vehicle: DF.Link
		vehicle_type: DF.Data | None
	# end: auto-generated types
	pass
