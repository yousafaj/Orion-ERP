# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class VehicleDeployment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from orion_erp.orion_erp.doctype.deployment_checklist_item.deployment_checklist_item import DeploymentChecklistItem

		actual_end_date: DF.Date | None
		checklist: DF.Table[DeploymentChecklistItem]
		condition_notes: DF.SmallText | None
		customer: DF.Link | None
		driver: DF.Link | None
		driver_name: DF.Data | None
		ended_because: DF.Literal["", "Driver Replaced", "Vehicle Replaced", "Job Completed"]
		expected_end_date: DF.Date | None
		fuel_level: DF.Literal["Full", "3/4", "1/2", "1/4", "Empty"]
		mobilization_date: DF.Date | None
		mobilization_order: DF.Link | None
		replaced_by: DF.Link | None
		replacement_of: DF.Link | None
		replacement_reason: DF.SmallText | None
		site: DF.Data | None
		site_location: DF.Data | None
		start_odometer: DF.Int
		status: DF.Literal["", "Mobilized", "Demobilized"]
		sub_location: DF.Data | None
		vehicle: DF.Link | None
		vehicle_type: DF.Data | None
	# end: auto-generated types
	pass
