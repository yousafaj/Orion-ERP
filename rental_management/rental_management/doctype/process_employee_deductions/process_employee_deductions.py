# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt,getdate



class ProcessEmployeeDeductions(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.process_employee_deduction_detail.process_employee_deduction_detail import ProcessEmployeeDeductionDetail

		amended_from: DF.Link | None
		employee_category: DF.Literal["", "Office", "Non-Office"]
		naming_series: DF.Literal[None]
		outstanding_installments: DF.Table[ProcessEmployeeDeductionDetail]
		payroll_date_date: DF.Date | None
		payroll_month: DF.Literal["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
		payroll_start_date: DF.Date | None
		year: DF.Link
	# end: auto-generated types
	
	def validate(self):
		validate_duplicate_transaction(self)

		if self.outstanding_installments:
			return
		populate_outstanding_installments(self)

	def on_submit(self):
		validate_salary_slip_exists(self)
		create_additional_salary(self)

	def on_cancel(self):
		validate_salary_slip_before_cancel(self)
		cancel_linked_additional_deductions(self)


def cancel_linked_additional_deductions(self):

	additional_salary_list = list(set([
		row.additional_salary_ref
		for row in self.outstanding_installments
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


def validate_duplicate_transaction(self):

	exists = frappe.db.exists(
		"Process Employee Deductions",
		{
			"name": ["!=", self.name],
			"docstatus": ["!=", 2],
			"year": self.year,
			"payroll_month": self.payroll_month,
			"employee_category": self.employee_category
		}
	)

	if exists:
		frappe.throw(
			f"Process Employee Deductions already exists for "
			f"Employee Category <b>{self.employee_category}</b>, "
			f"Month <b>{self.payroll_month}</b> "
			f"and Fiscal Year <b>{self.year}</b>"
		)

def populate_outstanding_installments(self):

		self.outstanding_installments = []

		employee_filters = {}

		# Employee Category Filter
		employee_filters["custom_employee_category"] = self.employee_category


		employees = frappe.get_all(
			"Employee",
			filters=employee_filters,
			fields=["name", "employee_name"]
		)

		for emp in employees:

			parent = frappe.get_all(
				"Employee Deduction",
				filters={
					"employee": emp.name,
					"docstatus": 1
				},
				fields=["name"],
				order_by="creation desc",
				limit=1
			)

			if not parent:
				continue

			doc = frappe.get_doc("Employee Deduction", parent[0].name)

			# ---------------- CURRENT TABLE ----------------
			for row in doc.employee_deduction_detail or []:

				if flt(row.remaining_amount) <= 0:
					continue
				if getdate(row.payroll_start_date) > getdate(self.payroll_date_date):
					continue
				installment_amount=min(row.installment_amount,row.remaining_amount)
				self.append("outstanding_installments", {
					"employee": doc.employee,
					"employee_name": doc.employee_name,
					"type_of_penalty": row.type_of_penalty,
					"date_of_deduction_occurred": row.deduction_date,
					"outstanding_amount": row.remaining_amount,
					"installment_amount": installment_amount,
					"employee_deduction_reference":row.name,
					"employee_deduction_parent_reference":row.parent,
					"amount_to_be_deducted_this_month": installment_amount
				})

			# ---------------- OUTSTANDING TABLE ----------------
			for row in doc.outstanding_employee_deduction_detail or []:

				if flt(row.remaining_amount) <= 0:
					continue
				if getdate(row.payroll_start_date) > getdate(self.payroll_date_date):
					continue
				installment_amount=min(row.installment_amount,row.remaining_amount)
				self.append("outstanding_installments", {
					"employee": doc.employee,
					"employee_name": doc.employee_name,
					"type_of_penalty": row.type_of_penalty,
					"date_of_deduction_occurred": row.deduction_date,
					"outstanding_amount": row.remaining_amount,
					"installment_amount": installment_amount,
					"employee_deduction_reference": row.name,
					"employee_deduction_parent_reference":row.parent,
					"amount_to_be_deducted_this_month": installment_amount
				})

def create_additional_salary(self):

	employee_wise_data = {}

	for row in self.outstanding_installments:

		if row.skip_penalty_amount:
			continue

		if not row.employee:
			continue

		# AMOUNT SHOULD BE > 0
		if flt(
			row.amount_to_be_deducted_this_month
		) <= 0:
			continue

		if row.employee not in employee_wise_data:

			employee_wise_data[
				row.employee
			] = []

		employee_wise_data[
			row.employee
		].append(row)

	for employee, rows in employee_wise_data.items():

		total_amount = sum([
			flt(
				d.amount_to_be_deducted_this_month
			)
			for d in rows
		])

		if total_amount <= 0:
			continue

		# CHECK EXISTING ADDITIONAL SALARY
		existing_salary = frappe.db.exists(
			"Additional Salary",
			{
				"employee": employee,
				"payroll_date":
					self.payroll_date_date,

				"salary_component":
					"Total Deduction",

				"overwrite_salary_structure_amount":
					1,

				"docstatus": ["!=", 2]
			}
		)

		if existing_salary:

			link = frappe.utils.get_link_to_form(
				"Additional Salary",
				existing_salary
			)

			frappe.throw(
				f"""
				<b>
					Additional Salary Already Exists
				</b>

				<br><br>

				System found an existing
				Additional Salary for:

				<br><br>

				Employee:
				<b>{employee}</b>

				<br>

				Payroll Date:
				<b>{self.payroll_date_date}</b>

				<br><br>

				Please cancel the existing
				Additional Salary first.

				<br><br>

				Reference:
				{link}
				"""
			)

		# FETCH EMPLOYEE DETAILS
		employee_doc = frappe.get_doc(
			"Employee",
			employee
		)

		# CREATE ADDITIONAL SALARY
		additional_salary = frappe.new_doc(
			"Additional Salary"
		)

		additional_salary.employee = employee

		additional_salary.company = (
			employee_doc.company
		)

		additional_salary.payroll_date = (
			self.payroll_date_date
		)

		additional_salary.salary_component = (
			"Total Deduction"
		)

		additional_salary.amount = (
			total_amount
		)

		additional_salary.overwrite_salary_structure_amount = 1

		additional_salary.custom_auto_generated = 1

		additional_salary.custom_reference_ = (
			self.name
		)

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

def validate_salary_slip_before_cancel(self):
	employees = list(
		set([
			row.employee
			for row in self.outstanding_installments
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
					getdate(self.payroll_date_date)
				],
				"end_date": [
					">=",
					getdate(self.payroll_start_date)
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

	# THROW ERROR
	if salary_slips:

		message = """
		<b>Cannot Cancel Process Employee Deduction</b>
		<br><br>

		Following submitted Salary Slips exist
		for the selected payroll period.
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

def validate_salary_slip_exists(self):

	from frappe.utils import getdate

	employees = list(
		set([
			row.employee
			for row in self.outstanding_installments
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
					getdate(self.payroll_date_date)
				],
				"end_date": [
					">=",
					getdate(self.payroll_start_date)
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

	# THROW ERROR
	if salary_slips:

		message = f"""
		<b>Salary Slips Already Exist</b>
		<br><br>

		Salary Slips are already created for the selected payroll period:
		<br>
		<b>
			{self.payroll_start_date}
			to
			{self.payroll_date_date}
		</b>

		<br><br>

		Please cancel the below Salary Slips first,
		then submit this Process Employee Deduction document.
		<br><br>
		"""

		for slip in salary_slips:

			message += f"""
			<li>
				<b>{slip.name}</b>
				-
				{slip.employee_name}

				<br>

				Payroll Period:
				{slip.start_date} to {slip.end_date}
			</li>
			"""

		frappe.throw(message)