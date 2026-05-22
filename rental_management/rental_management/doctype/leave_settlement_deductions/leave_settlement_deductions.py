# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class LeaveSettlementDeductions(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		additional_deduction_ref: DF.Link | None
		additional_salary_ref: DF.Data | None
		amount_to_be_deducted_this_month: DF.Currency
		date_of_deduction_occurred: DF.Date | None
		employee: DF.Link | None
		employee_deduction_parent_reference: DF.Link | None
		employee_deduction_reference: DF.Data | None
		employee_name: DF.Data | None
		installment_amount: DF.Currency
		outstanding_amount: DF.Currency
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		skip_penalty_amount: DF.Check
		type_of_penalty: DF.Link | None
	# end: auto-generated types
	pass
