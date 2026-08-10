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
		from orion_erp.orion_erp.doctype.asset_detail.asset_detail import AssetDetail

		actual_rejoining_date: DF.Date
		amended_from: DF.Link | None
		approved_rejoining_date: DF.Date
		assets: DF.TableMultiSelect[AssetDetail]
		company: DF.Link | None
		custom_cancelled_leave_application: DF.Data | None
		custom_created_leave_application: DF.Data | None
		custom_employee_user_id: DF.Link | None
		custom_last_status_change: DF.Datetime | None
		custom_rejoining_approval_status: DF.Literal["Open", "Pending Approval from Approver 1", "Pending Approval from Approver 2", "Pending Approval from Approver 3", "Pending Approval from Approver 4", "Pending Approval from Approver 5", "Submit Pending", "Approved", "Rejected", "Cancelled"]
		custom_rejoining_approver_1: DF.Link | None
		custom_rejoining_approver_2: DF.Link | None
		custom_rejoining_approver_3: DF.Link | None
		custom_rejoining_approver_4: DF.Link | None
		custom_rejoining_approver_5: DF.Link | None
		custom_status_rejoining_approver1: DF.Literal["Open", "Approved", "Rejected", "Cancelled"]
		custom_status_rejoining_approver2: DF.Literal["Open", "Approved", "Rejected", "Cancelled"]
		custom_status_rejoining_approver3: DF.Literal["Open", "Approved", "Rejected", "Cancelled"]
		custom_status_rejoining_approver4: DF.Literal["Open", "Approved", "Rejected", "Cancelled"]
		custom_status_rejoining_approver5: DF.Literal["Open", "Approved", "Rejected", "Cancelled"]
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
		leave_application: DF.Link | None
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
