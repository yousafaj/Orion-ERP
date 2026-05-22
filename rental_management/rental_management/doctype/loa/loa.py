# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class LOA(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.loa_locations_cdt.loa_locations_cdt import LOAlocationscdt

		active: DF.Check
		allocated_driver_quota: DF.Int
		allocated_vehicle_quota: DF.Int
		amended_from: DF.Link | None
		contract_number: DF.Data
		contract_year: DF.Int
		document: DF.Attach | None
		end_user: DF.Link
		expiry_date: DF.Date
		issue_date: DF.Date
		issuing_authority: DF.Link
		license_expiry_date: DF.Date | None
		license_issue_date: DF.Date | None
		loa_status: DF.Literal["", "Active", "Expired"]
		locations: DF.Table[LOAlocationscdt]
		mother_attachment: DF.Attach | None
		ref_no: DF.Data
		remaining_driver_quota: DF.Int
		remaining_vehicle_quota: DF.Int
		total_cancelled_driver_cicpa: DF.Int
		total_cancelled_vehicle_cicpa: DF.Int
		total_created_driver_cicpa: DF.Int
		total_created_vehicle_cicpa: DF.Int
		total_driver_quota: DF.Int
		total_vehicle_quota: DF.Int
	# end: auto-generated types
	pass
