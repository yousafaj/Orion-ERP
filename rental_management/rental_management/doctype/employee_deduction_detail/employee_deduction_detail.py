# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class EmployeeDeductionDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		additional_deduction_ref: DF.Text | None
		amount_paid_by_employee_to_gov: DF.Currency
		attachment_1: DF.Attach | None
		attachment_2: DF.Attach | None
		attachment_3: DF.Attach | None
		deduction_amount: DF.Currency
		deduction_date: DF.Date
		installment: DF.Int
		installment_amount: DF.Currency
		paid: DF.Check
		paid_amount: DF.Currency
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		partial_paid: DF.Check
		partial_paid_amount: DF.Currency
		payrol_end_date: DF.Date | None
		payroll_start_date: DF.Date
		reference: DF.Text | None
		remaining_amount: DF.Currency
		remarks: DF.Text | None
		status: DF.Literal["", "Unpaid", "Partial Paid", "Paid"]
		type_of_penalty: DF.Link
	# end: auto-generated types
	pass
