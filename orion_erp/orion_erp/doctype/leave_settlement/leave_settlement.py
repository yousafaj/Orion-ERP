# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate,flt
import re

class LeaveSettlement(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from orion_erp.orion_erp.doctype.gratuity_pay.gratuity_pay import GratuityPay
		from orion_erp.orion_erp.doctype.leave_pay.leave_pay import LeavePay
		from orion_erp.orion_erp.doctype.leave_settlement_deductions.leave_settlement_deductions import LeaveSettlementDeductions
		from orion_erp.orion_erp.doctype.salary_due.salary_due import SalaryDue
		from orion_erp.orion_erp.doctype.ticket_allowance.ticket_allowance import TicketAllowance

		adjustments_if_any: DF.Currency
		amended_from: DF.Link | None
		company: DF.Link
		date_of_settlement: DF.Date
		department: DF.Link | None
		doj__re_joining_date: DF.Date | None
		employee: DF.Link
		employee_name: DF.Data | None
		gratuity_pay: DF.Table[GratuityPay]
		last_working_day: DF.Date | None
		leave_pay: DF.Table[LeavePay]
		leave_settlement_deductions: DF.Table[LeaveSettlementDeductions]
		monthly_salary: DF.Currency
		other_allowance: DF.Currency
		other_deduction: DF.Currency
		outstanding_advance: DF.Currency
		overtime_allowance: DF.Currency
		position: DF.Link | None
		posting_date: DF.Date | None
		remark: DF.LongText | None
		salary_due: DF.Table[SalaryDue]
		ticket_allowance: DF.Table[TicketAllowance]
		total_deductions: DF.Currency
		total_entitlements: DF.Currency
		total_service: DF.Data | None
		total_settlement_payable: DF.Currency
		traffic_fine: DF.Currency
		type_of_settlement: DF.Literal["", "Vacation Settlement", "Final Settlement", "Labour Court Settlement", "Internal Transfer Settlement"]
	# end: auto-generated types
	@frappe.whitelist()
	def populate_leave_settlement_deductions(self):

		self.leave_settlement_deductions = []

		if not self.employee:
			return

		parent = frappe.get_all(
			"Employee Deduction",
			filters={
				"employee": self.employee,
				"docstatus": 1
			},
			fields=["name"],
			order_by="creation desc",
			limit=1
		)

		if not parent:
			return

		doc = frappe.get_doc("Employee Deduction", parent[0].name)

		# ---------------- CURRENT TABLE ----------------
		for row in doc.employee_deduction_detail or []:

			if flt(row.remaining_amount) <= 0:
				continue

			installment_amount = flt(row.remaining_amount)


			self.append("leave_settlement_deductions", {
				"employee": doc.employee,
				"employee_name": doc.employee_name,
				"type_of_penalty": row.type_of_penalty,
				"date_of_deduction_occurred": row.deduction_date,
				"outstanding_amount": row.remaining_amount,
				"installment_amount": installment_amount,
				"employee_deduction_reference": row.name,
				"employee_deduction_parent_reference": row.parent,
				"amount_to_be_deducted_this_month": installment_amount
			})

		# ---------------- OUTSTANDING TABLE ----------------
		for row in doc.outstanding_employee_deduction_detail or []:

			if flt(row.remaining_amount) <= 0:
				continue

			installment_amount = flt(row.remaining_amount)
			

			self.append("leave_settlement_deductions", {
				"employee": doc.employee,
				"employee_name": doc.employee_name,
				"type_of_penalty": row.type_of_penalty,
				"date_of_deduction_occurred": row.deduction_date,
				"outstanding_amount": row.remaining_amount,
				"installment_amount": installment_amount,
				"employee_deduction_reference": row.name,
				"employee_deduction_parent_reference": row.parent,
				"amount_to_be_deducted_this_month": installment_amount
			})

	def on_submit(self):
		mark_ticket_paid(self)
		
		create_leave_settlement_deduction(self)

	def validate(self):
		validate_ticket_allowance(self)

	def on_cancel(self):
		revert_ticket_paid(self)
		cancel_linked_additional_deductions(self)
		validate_salary_slip_before_cancel(self)


def create_leave_settlement_deduction(self):
	if not self.leave_settlement_deductions:
		return

	rows = []

	for d in self.leave_settlement_deductions:

		if d.skip_penalty_amount:
			continue

		if flt(d.amount_to_be_deducted_this_month) <= 0:
			continue


		rows.append(d)

	if not rows:
		return

	total_amount = sum(
		flt(d.amount_to_be_deducted_this_month)
		for d in rows
	)

	additional_salary = frappe.new_doc(
		"Additional Salary"
	)

	additional_salary.employee = self.employee

	additional_salary.employee_name = self.employee_name

	additional_salary.company = self.company

	additional_salary.payroll_date = self.date_of_settlement

	additional_salary.salary_component = "Total Deduction"

	additional_salary.currency = frappe.get_cached_value(
		"Company",
		self.company,
		"default_currency"
	)

	additional_salary.amount = total_amount

	additional_salary.overwrite_salary_structure_amount = 1

	additional_salary.custom_auto_generated = 1

	additional_salary.custom_reference_ = self.name

	# APPEND PENALTY CHILD ROWS
	for d in rows:

		additional_salary.append(
			"custom_penalties_detail",
			{
				"penalty_name":
					d.type_of_penalty,

				"installation_amount":
					d.amount_to_be_deducted_this_month,

				"employee_deduction_reference":
					d.employee_deduction_reference,

				"date_of_deduction_occurred":
					d.date_of_deduction_occurred,

				"remaining_amount":
					d.outstanding_amount
			}
		)

	# INSERT & SUBMIT
	additional_salary.insert(
		ignore_permissions=True
	)

	additional_salary.submit()

	# STORE ADDITIONAL SALARY REF
	for d in rows:

		d.db_set(
			"additional_salary_ref",
			additional_salary.name,
			update_modified=False
		)

@frappe.whitelist()
def get_ticket_allowance(employee, settlement_date):
	"""
	Returns unpaid Ticket Allowance records for an employee where the
	settlement date falls within the allowance cycle.
	"""

	if not employee or not settlement_date:
		return []

	
	settlement_date = getdate(settlement_date)

	# Fetch ticket allowance records that match the settlement date
	tickets = frappe.get_all(
		"Ticket Allowance Detail",
		filters={
			"parent": employee,                
			"parenttype": "Employee",
			"paid": 0,
			"manual_paid":0,                         
			"from_date": ["<=", settlement_date],  
			"to_date": [">=", settlement_date]     
		},
		fields=["from_date", "to_date", "outstanding_amount"],
		order_by="from_date asc"
	)

	result = []

	# Format data to match the structure expected by the client script
	for t in tickets:
		result.append({
			"from": t.from_date,
			"to": t.to_date,
			"amount": t.outstanding_amount
		})
	
	return result

def mark_ticket_paid(doc, method=None):

	if not doc.ticket_allowance:
		return

	for row in doc.ticket_allowance:

		ticket_detail = frappe.db.get_value(
			"Ticket Allowance Detail",
			{
				"parent": doc.employee,
				"from_date": row.get("from")
			},
			[
				"name",
				"amount",
				"paid_amount",
				"references_data"
			],
			as_dict=True
		)

		if not ticket_detail:
			continue

		current_paid_amount = flt(
			ticket_detail.paid_amount
		)

		row_amount = flt(row.amount)

		total_paid_amount = (
			current_paid_amount + row_amount
		)

		total_amount = flt(
			ticket_detail.amount
		)

		outstanding_amount = max(
			0,
			total_amount - total_paid_amount
		)

		# ============================================
		# EXISTING HTML
		# ============================================

		existing_reference = (
			ticket_detail.references_data or ""
		)

		new_row = f"""
			<tr>
				<td>
					<a href="/app/leave-settlement/{doc.name}">
						{doc.name}
					</a>
				</td>

				<td>{doc.date_of_settlement}</td>

				<td>{row_amount}</td>
			</tr>
		"""

		if not existing_reference:

			reference_table = f"""
				<div class="table-responsive">
					<table class="table table-bordered">
						<thead>
							<tr>
								<th>Leave Settlement</th>
								<th>Date Of Settlement</th>
								<th>Amount</th>
							</tr>
						</thead>

						<tbody>
							{new_row}
						</tbody>
					</table>
				</div>
			"""

		else:

			reference_table = existing_reference.replace(
				"</tbody>",
				f"{new_row}</tbody>"
			)

		update_data = {
			"paid_amount": total_paid_amount,
			"outstanding_amount": outstanding_amount,
			"references_data": reference_table
		}

		if total_paid_amount >= total_amount:

			update_data["paid"] = 1
			update_data["partial_paid"] = 0

		else:

			update_data["paid"] = 0
			update_data["partial_paid"] = 1

		frappe.db.set_value(
			"Ticket Allowance Detail",
			ticket_detail.name,
			update_data
		)


def validate_ticket_allowance(doc):

	if not doc.ticket_allowance:
		return

	for row in doc.ticket_allowance:

		outstanding_amount = frappe.db.get_value(
			"Ticket Allowance Detail",
			{
				"parent": doc.employee,
				"from_date": row.get("from")
			},
			"outstanding_amount"
		)

		outstanding_amount = flt(
			outstanding_amount
		)

		row_amount = flt(row.amount)

		if row_amount > outstanding_amount:

			frappe.throw(
				f"""
				Row #{row.idx}: Ticket Allowance Amount
				cannot be greater than Outstanding Amount
				({outstanding_amount})
				"""
			)


def revert_ticket_paid(doc, method=None):

	if not doc.ticket_allowance:
		return

	for row in doc.ticket_allowance:

		ticket_detail = frappe.db.get_value(
			"Ticket Allowance Detail",
			{
				"parent": doc.employee,
				"from_date": row.get("from")
			},
			[
				"name",
				"amount",
				"paid_amount",
				"references_data"
			],
			as_dict=True
		)

		if not ticket_detail:
			continue

		current_paid_amount = flt(
			ticket_detail.paid_amount
		)

		row_amount = flt(row.amount)

		total_paid_amount = max(
			0,
			current_paid_amount - row_amount
		)

		total_amount = flt(
			ticket_detail.amount
		)

		outstanding_amount = (
			total_amount - total_paid_amount
		)

		reference_html = (
			ticket_detail.references_data or ""
		)

		pattern = rf"""
			<tr>\s*
				<td>\s*
					<a[^>]*>\s*
						{re.escape(doc.name)}
					\s*</a>\s*
				</td>\s*

				<td>\s*
					{re.escape(str(doc.date_of_settlement))}
				\s*</td>\s*

				<td>\s*
					{re.escape(str(row_amount))}
				\s*</td>\s*
			</tr>
		"""

		reference_html = re.sub(
			pattern,
			"",
			reference_html,
			flags=re.S | re.X
		)

		paid = 0
		partial_paid = 0

		if total_paid_amount > 0:
			partial_paid = 1

		if total_paid_amount >= total_amount:
			paid = 1
			partial_paid = 0

		frappe.db.set_value(
			"Ticket Allowance Detail",
			ticket_detail.name,
			{
				"paid_amount": total_paid_amount,
				"outstanding_amount": outstanding_amount,
				"paid": paid,
				"partial_paid": partial_paid,
				"references_data": reference_html
			}
		)


def cancel_linked_additional_deductions(self):

	additional_salary_list = list(set([
		row.additional_salary_ref
		for row in self.leave_settlement_deductions
		if row.additional_salary_ref
	]))

	if not additional_salary_list:
		return

	additional_deductions = frappe.get_all(
		"Additional Deduction",
		filters={
			"docstatus": 1,
			"ref_doctype": "Additional Salary",
			"ref_docname": ["in", additional_salary_list]
		},
		fields=["name"]
	)

	for d in additional_deductions:

		doc = frappe.get_doc("Additional Deduction", d.name)
		doc.cancel()



def validate_salary_slip_before_cancel(self):

	employees = list(
		set([
			row.employee
			for row in self.leave_settlement_deductions
			if row.employee
		])
	)

	if not employees:
		return

	salary_slips = []

	for employee in employees:

		slips = frappe.get_all(
			"Salary Slip",
			filters={
				"employee": employee,
				"docstatus": 1,
				"start_date": [
					"<=",
					getdate(self.date_of_settlement)
				],
				"end_date": [
					">=",
					getdate(self.date_of_settlement)
				]
			},
			fields=[
				"name",
				"employee",
				"employee_name",
				"start_date",
				"end_date"
			]
		)

		for slip in slips:
			salary_slips.append(slip)

	if salary_slips:

		message = """
		<b>Cannot Cancel Leave Settlement</b>
		<br><br>

		Following submitted Salary Slips exist
		for the settlement date.
		Please cancel them first.
		<br><br>
		"""

		for slip in salary_slips:

			message += f"""
			<li>
				<b>{slip.name}</b>
				- {slip.employee_name}
				({slip.start_date} to {slip.end_date})
			</li>
			"""

		frappe.throw(message)