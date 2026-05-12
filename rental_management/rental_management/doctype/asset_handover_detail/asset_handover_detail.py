# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AssetHandoverDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		asset_code: DF.Data | None
		asset_status: DF.Literal["Active", "Returned", "Lost", "Damaged"]
		asset_type: DF.Link
		attachment: DF.Attach | None
		brand: DF.Link | None
		brand_model: DF.Link | None
		card_issue_date: DF.Date | None
		card_number: DF.Data | None
		cicpa_status: DF.Literal["", "Active", "Expired"]
		condition: DF.Literal["New", "Used"]
		device_type: DF.Literal["Laptop", "Desktop"]
		expiry_date: DF.Date | None
		fuel_type: DF.Data | None
		imei_number: DF.Data | None
		issued_by: DF.Link
		issued_date: DF.Date
		it_brand: DF.Link | None
		it_model: DF.Link | None
		linked_account: DF.Link | None
		lost__reissued: DF.Literal["", "Yes", "No"]
		model: DF.Link | None
		mulkiya_expiry_uae_specific: DF.Data | None
		name_of_last_user: DF.Data | None
		network: DF.Data | None
		network_provider: DF.Data | None
		odometer_reading_at_issue: DF.Data | None
		odometer_reading_at_return: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		parking_slot_number: DF.Data | None
		parking_status: DF.Data | None
		pass_number: DF.Data | None
		plate_number: DF.Data | None
		qty: DF.Int
		remarks: DF.Text | None
		request_date: DF.Date | None
		return_date: DF.Date | None
		sim_card_number: DF.Data | None
		sim_number: DF.Data | None
		sim_status: DF.Literal["Active", "Inactive", "Returned", "Lost"]
		valid_to: DF.Date | None
		vehicle_cicpa_pass: DF.Data | None
		vehicle_type: DF.Link | None
	# end: auto-generated types
	pass
