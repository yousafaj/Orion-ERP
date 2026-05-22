# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class WarningLetter(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		absent_from_date: DF.Date | None
		absent_to_date: DF.Date | None
		actual_return_date: DF.Date | None
		amended_from: DF.Link | None
		approved_leave_days: DF.Float
		company: DF.Link
		consequence: DF.Text | None
		date: DF.Date | None
		details: DF.Text | None
		employee: DF.Link
		employee_name: DF.Data | None
		hr_manager: DF.Link
		hr_salutation: DF.Data | None
		incident_details: DF.Text | None
		leave_start_date: DF.Date | None
		leave_type: DF.Link | None
		mode_of_payment: DF.Literal["", "Cash", "WPS"]
		posting_date: DF.Date | None
		termination_date: DF.Date | None
		title: DF.Literal["", "Negligence of Work", "Warning for Physical Misconduct", "Safety Violation", "Leave Policy Violation", "Alcohol Consumption", "Not Following Company Policy", "Not Following Supervisor Instructions", "Misconduct Warning Letter", "Attendance Improvement Letter", "Diesel Theft", "Refusal to Work", "Poor Performance", "Termination of Employment", "Non Compliance with Company Policy", "Performance Improvement"]
		warning_template: DF.Link | None
	# end: auto-generated types
	pass
