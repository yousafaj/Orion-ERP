# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class REGULARINCENTIVE(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.salary_breakup_detail.salary_breakup_detail import SalaryBreakupDetail

		amended_from: DF.Link | None
		company: DF.Link
		currency: DF.Link | None
		details: DF.Table[SalaryBreakupDetail]
		effective_date: DF.Date
		employee: DF.Link
		employee_name: DF.Data | None
		salary_increment_amt: DF.Currency
		total_existing_monthly_salary: DF.Currency
		total_revised_monthly_salary: DF.Currency
	# end: auto-generated types
	pass
