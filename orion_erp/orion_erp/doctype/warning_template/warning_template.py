# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class WarningTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		absent_from_date: DF.Date | None
		absent_to_date: DF.Date | None
		actual_return_date: DF.Date | None
		approved_leave_days: DF.Float
		consequence: DF.Text | None
		date: DF.Date | None
		details: DF.Text | None
		incident_details: DF.Text | None
		leave_start_date: DF.Date | None
		leave_type: DF.Link | None
		title: DF.Literal["", "Negligence of Work", "Attendance Improvement Letter", "Warning for Physical Misconduct", "Leave Policy Violation", "Safety Violation", "Alcohol Consumption", "Not Following Supervisor Instructions"]
	# end: auto-generated types
	pass
