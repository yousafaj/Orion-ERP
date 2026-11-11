# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TrailWorkshopInterview(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		candidate_name: DF.Data
		date: DF.Date
		designation: DF.Data | None
		interview_evaluation_report: DF.Attach
		mob_no: DF.Phone
		name_of_examiner: DF.Data
		remarks_if_any: DF.SmallText | None
		status: DF.Literal["PASSED the test", "FAILED the test"]
	# end: auto-generated types
	pass
