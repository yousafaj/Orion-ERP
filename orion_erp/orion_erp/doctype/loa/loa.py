# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LOA(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from orion_erp.orion_erp.doctype.loa_locations_cdt.loa_locations_cdt import LOAlocationscdt

		active: DF.Check
		allocated_driver_quota: DF.Int
		allocated_vehicle_quota: DF.Int
		amended_from: DF.Link | None
		contract_number: DF.Data
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

	def validate(self):
		self._fill_location_codes()

	def _fill_location_codes(self):
		"""Keep the row code and the Location master in sync, both ways:
		  * blank row code  -> pull it from the Location;
		  * row code typed but Location has none -> save it back to the Location.
		Only block when a row has no code anywhere (owner wanted it never left blank)."""
		missing = []
		for row in self.locations or []:
			if not row.location:
				continue
			master_code = frappe.db.get_value("Location", row.location, "custom_location_code")
			if not row.location_code and master_code:
				row.location_code = master_code
			elif row.location_code and not master_code:
				frappe.db.set_value("Location", row.location, "custom_location_code", row.location_code)
			if not row.location_code:
				missing.append(row.location)
		if missing:
			frappe.throw(
				_("Enter a Location Code for: {0} (you can type it directly in the table).").format(
					", ".join(missing)
				)
			)


def auto_expire_loas():
	today = frappe.utils.nowdate()
	candidates = frappe.get_all(
		"LOA",
		filters={"docstatus": 1, "loa_status": "Active", "expiry_date": ["<", today]},
		pluck="name",
	)
	for name in candidates:
		try:
			frappe.db.set_value(
				"LOA",
				name,
				{"loa_status": "Expired", "active": 0},
				update_modified=True,
			)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"auto_expire_loas failed for {name}")
