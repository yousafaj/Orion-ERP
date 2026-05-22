# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RejoiningForm(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.asset_detail.asset_detail import AssetDetail

		actual_rejoining_date: DF.Date
		amended_from: DF.Link | None
		approved_rejoining_date: DF.Date
		assets: DF.TableMultiSelect[AssetDetail]
		company: DF.Link | None
		date_hr: DF.Date
		date_incharge: DF.Date
		department: DF.Link | None
		department_in_charge_id: DF.Link
		department_in_charge_name: DF.Data | None
		designation: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		hr_id: DF.Link
		hr_name: DF.Data | None
		leave_days_approved: DF.Data | None
		leave_end_date: DF.Date
		leave_start_date: DF.Date
		leave_type: DF.Link
		mobilization__date: DF.Date
		naming_series: DF.Literal[None]
		other: DF.Check
		other_declaration: DF.Data | None
		reporting_date: DF.Date
		reporting_location: DF.Data
		reporting_time: DF.Time
		site_allocated: DF.Data
		tentative_rejoining_date: DF.Date
	# end: auto-generated types
	pass
