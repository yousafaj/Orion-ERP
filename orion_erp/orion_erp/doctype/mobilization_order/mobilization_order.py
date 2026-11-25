# Place at: <your_app>/<your_module>/doctype/mobilization_order/mobilization_order.py
# Keep any lines that ERPNext already generated in this file; just make sure
# the import and the validate method below exist.
#
# CHANGE the import path to your real path of api.py.

from frappe.model.document import Document

from orion_erp.orion_erp.validations.fleet_oprations import validate_order

class MobilizationOrder(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from orion_erp.orion_erp.doctype.mobilization_order_vehicle.mobilization_order_vehicle import MobilizationOrderVehicle

		amended_from: DF.Link | None
		customer: DF.Link
		expected_end_date: DF.Date | None
		order_date: DF.Date | None
		planned_mobilization_date: DF.Date
		project: DF.Link
		remarks: DF.SmallText | None
		site_location: DF.Data | None
		total_assigned: DF.Int
		total_mobilized: DF.Int
		vehicles: DF.Table[MobilizationOrderVehicle]
		vehicles_required: DF.Int
	# end: auto-generated types
	def validate(self):
		validate_order(self)