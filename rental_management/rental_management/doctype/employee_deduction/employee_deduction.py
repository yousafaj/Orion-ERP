# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import re
from frappe.utils import get_first_day, get_last_day,getdate


class EmployeeDeduction(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.employee_deduction_detail.employee_deduction_detail import EmployeeDeductionDetail
		from rental_management.rental_management.doctype.outstanding_employee_deduction_detail.outstanding_employee_deduction_detail import OutstandingEmployeeDeductionDetail

		amended_from: DF.Link | None
		department: DF.Link | None
		employee: DF.Link | None
		employee_category: DF.Data | None
		employee_deduction_detail: DF.Table[EmployeeDeductionDetail]
		employee_name: DF.Data | None
		naming_series: DF.Literal[None]
		outstanding_employee_deduction_detail: DF.Table[OutstandingEmployeeDeductionDetail]
		paid_amount: DF.Currency
		remaining_balance: DF.Currency
		remarks: DF.Text | None
		status: DF.Literal["", "Draft", "Unpaid", "Partial Paid", "Paid"]
		total_deduction: DF.Currency
		transaction_date: DF.Date | None
	# end: auto-generated types
	pass

	def on_cancel(self):
		invalid_refs = []

		# check BOTH tables
		all_rows = (self.employee_deduction_detail or []) + (self.outstanding_employee_deduction_detail or [])

		for row in all_rows:
			if row.reference:

				refs = re.findall(r'>([^<]+)<', row.reference)

				for ref in refs:
					if frappe.db.get_value("Additional Salary", ref, "docstatus") == 1:
						invalid_refs.append(ref)

		if invalid_refs:
			frappe.throw(
				"Please cancel the following Additional Salary document(s) first:<br><b>"
				+ "<br>".join(set(invalid_refs)) +
				"</b>"
			)

	# VALIDATE
	def validate(self):
		self.update_child_payment()
		self.update_parent_totals()
		validate_installment_amount(self)

	# UPDATE AFTER SUBMIT
	def on_update_after_submit(self):

		if self.docstatus != 1:
			return
					
		self.update_child_payment()
		self.update_parent_totals()
		self.db_update()

		for row in self.employee_deduction_detail:
			row.db_update()

		for row in self.outstanding_employee_deduction_detail:
			row.db_update()

	
	# CHILD PAYMENT LOGIC
	def update_child_payment(self):

		all_rows = (self.employee_deduction_detail or []) + (self.outstanding_employee_deduction_detail or [])

		for row in all_rows:
			
			row.deduction_amount = row.deduction_amount or 0
			row.paid_amount = row.paid_amount or 0

			if row.paid and row.partial_paid:
				frappe.throw(f"Row {row.idx}: Cannot select both Paid and Partial Paid")

			if row.paid:
				row.paid_amount = row.deduction_amount
				row.remaining_amount = 0
				row.status = "Paid"

			elif row.partial_paid:

				if not row.partial_paid_amount or row.partial_paid_amount <= 0:
					frappe.throw(f"Row {row.idx}: Enter partial paid amount")

				if row.partial_paid_amount > row.remaining_amount:
					frappe.throw(f"Row {row.idx}: Partial amount exceeds remaining")

				row.paid_amount = min(
					row.deduction_amount,
					(row.paid_amount or 0) + row.partial_paid_amount
				)

				row.remaining_amount = row.deduction_amount - row.paid_amount
				row.status = "Paid" if row.remaining_amount == 0 else "Partial Paid"
				
				row.partial_paid_amount = 0
				row.partial_paid = 0

			else:
				row.remaining_amount = row.deduction_amount - row.paid_amount

				if row.paid_amount == 0:
					row.status = "Unpaid"
				elif row.remaining_amount == 0:
					row.status = "Paid"
				else:
					row.status = "Partial Paid"
			
			if abs(row.remaining_amount) < 0.001:
				row.remaining_amount = 0

			if row.doctype == "Employee Deduction Detail":
					sync_to_outstanding(self,row)


	# PARENT TOTALS
	def update_parent_totals(self):

		total = 0
		paid = 0
		remaining = 0

		total_rows = 0
		paid_rows = 0
		unpaid_rows = 0

		all_rows = (self.employee_deduction_detail or []) + (self.outstanding_employee_deduction_detail or [])

		for row in all_rows:

			total += row.deduction_amount or 0
			paid += row.paid_amount or 0
			remaining += row.remaining_amount or 0

			total_rows += 1

			if row.status == "Paid":
				paid_rows += 1
			elif row.status == "Unpaid":
				unpaid_rows += 1

		self.total_deduction = total
		self.paid_amount = paid
		self.remaining_balance = remaining

		# -------- STATUS --------
		if total_rows == 0:
			self.status = "Draft"
		elif paid_rows == total_rows:
			self.status = "Paid"
		elif unpaid_rows == total_rows:
			self.status = "Unpaid"
		else:
			self.status = "Partial Paid"

def validate_installment_amount(self):

	def check_rows(rows, table_name):
		for row in rows:

			# Skip if no value
			if row.installment_amount is None:
				continue

			if row.installment_amount <= 0:
				frappe.throw(
					f"{table_name} Row #{row.idx}: "
					"Installment Amount must be greater than 0"
				)

			# Installment must not exceed remaining
			if row.remaining_amount and row.installment_amount > row.remaining_amount:
				frappe.throw(
					f"{table_name} Row #{row.idx}: "
					f"Installment Amount ({row.installment_amount}) "
					f"cannot be greater than Remaining Amount ({row.remaining_amount})"
				)

	check_rows(self.employee_deduction_detail or [], "Employee Deduction Detail")
	check_rows(self.outstanding_employee_deduction_detail or [], "Outstanding Deduction Detail")

@frappe.whitelist()
def get_outstanding_penalties(employee):

	if not employee:
		return []

	result = []

	parent = frappe.get_all(
		"Employee Deduction",
		filters={
			"employee": employee,
			"docstatus": 1
		},
		fields=["name"],
		order_by="creation desc",
		limit=1
	)

	if not parent:
		return []

	doc = frappe.get_doc("Employee Deduction", parent[0].name)

	# ---------------- CURRENT TABLE ----------------
	for row in doc.employee_deduction_detail or []:

		if (row.remaining_amount or 0) <= 0:
			continue

		result.append({
			"type_of_penalty": row.type_of_penalty,
			"deduction_date": row.deduction_date,
			"payroll_start_date": row.payroll_start_date,
			"payrol_end_date": row.payrol_end_date,
			"deduction_amount": row.deduction_amount,
			"installment": row.installment,
			"installment_amount": row.installment_amount,
			"paid_amount": row.paid_amount,
			"remaining_amount": row.remaining_amount,
			"status": row.status,
			"reference": row.reference,
			"remarks": row.remarks,
			"attachment_1": row.attachment_1,
			"attachment_2": row.attachment_2,
			"parent_ref": parent[0].name,
			"child_ref": row.name,
			"source": "current",
			"additional_deduction_ref":row.additional_deduction_ref
		})

	# ---------------- OUTSTANDING TABLE ----------------
	for row in doc.outstanding_employee_deduction_detail or []:

		if (row.remaining_amount or 0) <= 0:
			continue

		result.append({
			"type_of_penalty": row.type_of_penalty,
			"deduction_date": row.deduction_date,
			"payroll_start_date": row.payroll_start_date,
			"payrol_end_date": row.payrol_end_date,
			"deduction_amount": row.deduction_amount,
			"installment": row.installment,
			"installment_amount": row.installment_amount,
			"paid_amount": row.paid_amount,
			"remaining_amount": row.remaining_amount,
			"status": row.status,
			"reference": row.reference,
			"remarks": row.remarks,
			"attachment_1": row.attachment_1,
			"attachment_2": row.attachment_2,
			"parent_ref": parent[0].parent_ref,
			"child_ref": row.child_ref,
			"source": "outstanding",
			"additional_deduction_ref":row.additional_deduction_ref
		})

	return result


@frappe.whitelist()
def run_deduction_cron():

	settings = frappe.get_single("Orion Settings")
	today = getdate()

	cron_oe = (
		getdate(settings.cron_schedule_date_oe)
		if settings.cron_schedule_date_oe
		else None
	)

	cron_noe = (
		getdate(settings.cron_schedule_date_noe)
		if settings.cron_schedule_date_noe
		else None
	)

	# ---------------- OFFICE ----------------
	if cron_oe and today == cron_oe:

		end_date = get_last_day(settings.payroll_month_date_oe)

		process_deductions(
			"Office",
			settings.payroll_month_date_oe
		)

		settings.db_set(
			"last_month_for_which_payment_processed_oe",
			end_date,
			update_modified=False
		)

	# ---------------- NON-OFFICE ----------------
	if cron_noe and today == cron_noe:

		end_date = get_last_day(settings.payroll_month_date_noe)

		process_deductions(
			"Non-Office",
			settings.payroll_month_date_noe
		)

		settings.db_set(
			"last_month_for_which_payment_processed_noe",
			end_date,
			update_modified=False
		)



# PROCESS DEDUCTIONS
def process_deductions(category, payroll_date):

	if not payroll_date:
		return

	payroll_date = getdate(payroll_date)

	start_date = get_first_day(payroll_date)
	end_date = get_last_day(payroll_date)

	employees = frappe.get_all(
		"Employee",
		filters={
			"custom_employee_category": category
		},
		pluck="name"
	)

	for emp in employees:

		try:
			if frappe.db.exists(
				"Additional Salary",
				{
					"employee": emp,
					"payroll_date": end_date,
					"salary_component": "Total Deduction",
					"docstatus": 1
				}
			):
				continue


			doc_name = frappe.db.get_value(
				"Employee Deduction",
				{
					"employee": emp,
					"docstatus": 1
				},
				"name",
				order_by="creation desc"
			)

			if not doc_name:
				continue

			doc = frappe.get_doc(
				"Employee Deduction",
				doc_name
			)

			picked_rows = []


			for row in doc.employee_deduction_detail or []:

				if (row.remaining_amount or 0) <= 0:
					continue

				if not row.payroll_start_date:
					continue

				row_start = row.payroll_start_date
				row_end = row.payrol_end_date or end_date

				if not (
					row_start <= end_date
					and row_end >= start_date
				):
					continue

				picked_rows.append({
					"row": row,
					"doctype": "Employee Deduction Detail"
				})

			
			# OUTSTANDING DEDUCTIONS
			for row in doc.outstanding_employee_deduction_detail or []:

				if (row.remaining_amount or 0) <= 0:
					continue

				if not row.payroll_start_date:
					continue

				row_start = row.payroll_start_date
				row_end = row.payrol_end_date or end_date

				if not (
					row_start <= end_date
					and row_end >= start_date
				):
					continue

				picked_rows.append({
					"row": row,
					"doctype": "Outstanding Employee Deduction Detail"
				})

			if not picked_rows:
				continue

			# CREATE ADDITIONAL SALARY
			create_additional_salary(
				emp,
				end_date,
				picked_rows
			)

			frappe.db.commit()

		except Exception:

			frappe.db.rollback()

			frappe.log_error(
				title=f"Deduction Cron Failed for Employee {emp}",
				message=frappe.get_traceback()
			)

			continue



# CREATE ADDITIONAL SALARY
def create_additional_salary(employee, payroll_date, picked_rows):

	emp = frappe.get_doc("Employee", employee)

	doc = frappe.new_doc("Additional Salary")
	doc.employee = employee
	doc.company = emp.company
	doc.salary_component = "Total Deduction"
	doc.payroll_date = payroll_date
	doc.custom_auto_generated=1

	total = 0

	for item in picked_rows:

		row = item["row"]

		installment = min(
			row.installment_amount or 0,
			row.remaining_amount or 0
		)

		if installment <= 0:
			continue

		child = doc.append("custom_penalties_detail", {})

		child.employee_deduction_reference = row.name
		child.penalty_name = row.type_of_penalty
		child.remaining_amount = row.remaining_amount
		child.installation_amount = installment
		child.deduction_date = row.deduction_date
		child.remarks = row.remarks

		total += installment

	if total <= 0:
		return

	doc.amount = total

	doc.insert(ignore_permissions=True)
	doc.submit()

	return doc

def sync_to_outstanding(self, row):

	if not (row.has_value_changed("paid") or row.has_value_changed("partial_paid")):
		return

	match_row = frappe.db.sql("""
		SELECT name, parent_ref, child_ref,parent
		FROM `tabOutstanding Employee Deduction Detail`
		WHERE parent_ref = %s
		ORDER BY creation DESC
		LIMIT 1
	""", (self.name,), as_dict=True)

	if not match_row:
		return

	match_row = match_row[0]

	# UPDATE CHILD
	if match_row.child_ref:

		frappe.db.sql("""
			UPDATE `tabOutstanding Employee Deduction Detail`
			SET
				paid_amount = %s,
				remaining_amount = %s,
				status = %s
			WHERE name = %s
		""", (
			row.paid_amount,
			row.remaining_amount,
			row.status,
			match_row.name
		))

	# UPDATE PARENT TOTALS
	if match_row.parent_ref:

		parent_doc = frappe.get_doc("Employee Deduction", match_row.parent)

		parent_doc.update_parent_totals()

		frappe.db.set_value(
			"Employee Deduction",
			parent_doc.name,
			{
				"paid_amount": parent_doc.paid_amount,
				"remaining_balance": parent_doc.remaining_balance,
				"status": parent_doc.status
			},
			update_modified=False
		)