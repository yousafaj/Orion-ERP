# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
import re
from frappe.utils import getdate


def execute(filters=None):

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data


def get_columns(filters=None):

	filters = filters or {}

	columns = [
		{
			"label": "Deduction Doc",
			"fieldname": "parent",
			"fieldtype": "Link",
			"options": "Employee Deduction",
			"width": 180
		},
		{
			"label": "Employee",
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150
		},
		{
			"label": "Employee Name",
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 220
		},
		{
			"label": "Penalty Type",
			"fieldname": "type_of_penalty",
			"fieldtype": "Link",
			"options": "Penalties",
			"width": 200
		},
		{
			"label": "Deduction Date",
			"fieldname": "deduction_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": "Payroll Start",
			"fieldname": "payroll_start_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": "Deduction Amount",
			"fieldname": "deduction_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": "Amount Paid By Employee to Gov",
			"fieldname": "amount_paid_by_employee_to_gov",
			"fieldtype": "Currency",
			"width": 220
		}
	]

	# SHOW/HIDE PAID AMOUNT
	if filters.get("show_paid_amount"):

		columns.append({
			"label": "Paid Amount",
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"width": 140
		})

	columns.extend([
		{
			"label": "Remaining Balance",
			"fieldname": "remaining_amount",
			"fieldtype": "Currency",
			"width": 160
		},
		{
			"label": "Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Salary Payroll Date",
			"fieldname": "additional_salary_date",
			"fieldtype": "Date",
			"width": 160
		},
		{
			"label": "Remarks",
			"fieldname": "remarks",
			"fieldtype": "Data",
			"width": 250
		},
	])

	return columns


def get_data(filters):

	filters = filters or {}

	conditions = ""
	values = {}

	# EMPLOYEE FILTER
	if filters.get("employee"):
		conditions += """
			AND ed.employee = %(employee)s
		"""
		values["employee"] = filters.get("employee")

	# STATUS FILTER
	if filters.get("status"):
		conditions += """
			AND edd.status = %(status)s
		"""
		values["status"] = filters.get("status")

	# PENALTY FILTER
	if filters.get("penalty_type"):
		conditions += """
			AND edd.type_of_penalty = %(penalty_type)s
		"""
		values["penalty_type"] = filters.get("penalty_type")

	# DEDUCTION DATE FILTER
	if filters.get("deduction_date"):
		conditions += """
			AND edd.deduction_date >= %(deduction_date)s
		"""
		values["deduction_date"] = (
			filters.get("deduction_date")
		)

	# PAYROLL START FILTER
	if filters.get("payroll_start_date"):
		conditions += """
			AND edd.payroll_start_date >= %(payroll_start_date)s
		"""
		values["payroll_start_date"] = (
			filters.get("payroll_start_date")
		)

	# PAYROLL END FILTER
	if filters.get("payroll_end_date"):

		conditions += """
			AND 
				edd.payroll_start_date <= %(payroll_end_date)s
		"""

		values["payroll_end_date"] = (
			filters.get("payroll_end_date")
		)

	data = frappe.db.sql(
		f"""
		SELECT
			edd.name as edd_name,
			edd.parent,
			ed.employee,
			ed.employee_name,
			edd.type_of_penalty,
			edd.deduction_date,
			edd.payroll_start_date,
			edd.deduction_amount,
			edd.amount_paid_by_employee_to_gov,
			edd.remaining_amount,
			edd.status,
			edd.remarks,
			edd.reference

		FROM `tabEmployee Deduction Detail` edd

		INNER JOIN `tabEmployee Deduction` ed
			ON ed.name = edd.parent

		WHERE ed.docstatus = 1
		{conditions}

		ORDER BY
			ed.employee,
			edd.deduction_date,
			edd.name
		""",
		values,
		as_dict=1
	)

	final_data = []

	for row in data:

		salary_list = []

		if row.get("reference"):

			salary_list = re.findall(
				r'>(HR-ADA-[^<]+)<',
				row.get("reference")
			)

		deduction_amount = (
			row.get("deduction_amount") or 0
		)

		gov_paid_amount = (
			row.get("amount_paid_by_employee_to_gov") or 0
		)

		running_balance = deduction_amount

		first_row = True

		# NO ADDITIONAL SALARY
		if not salary_list:

			gov_remaining_balance = (
				running_balance - gov_paid_amount
			)

			if gov_remaining_balance < 0:
				gov_remaining_balance = 0

			final_data.append({
				"parent": row.parent,
				"employee": row.employee,
				"employee_name": row.employee_name,
				"type_of_penalty": row.type_of_penalty,
				"deduction_date": row.deduction_date,
				"payroll_start_date": row.payroll_start_date,
				"deduction_amount": deduction_amount,
				"amount_paid_by_employee_to_gov":
					gov_paid_amount,
				"paid_amount": 0,
				"remaining_amount":
					gov_remaining_balance,
				"status": row.status,
				"remarks": row.remarks,
				"additional_salary_date": ""
			})

			continue

		for sal in salary_list:

			try:

				sal_doc = frappe.get_doc(
					"Additional Salary",
					sal
				)

			except Exception:
				continue

			# SALARY DATE FILTER
			if filters.get("salary_date"):

				if not sal_doc.payroll_date:
					continue

				if (
					getdate(sal_doc.payroll_date)
					< getdate(filters.get("salary_date"))
				):
					continue

			actual_paid_amount = 0

			# FETCH ACTUAL PAID AMOUNT
			for d in sal_doc.custom_penalties_detail or []:

				if (
					d.employee_deduction_reference
					== row.edd_name
				):

					actual_paid_amount += (
						d.installation_amount or 0
					)

			# PAYROLL DEDUCTION ROW
			if actual_paid_amount > 0:

				running_balance -= actual_paid_amount

				if running_balance < 0:
					running_balance = 0

				final_data.append({
					"parent":
						row.parent if first_row else "",

					"employee":
						row.employee if first_row else "",

					"employee_name":
						row.employee_name if first_row else "",

					"type_of_penalty":
						row.type_of_penalty if first_row else "",

					"deduction_date":
						row.deduction_date if first_row else "",

					"payroll_start_date":
						row.payroll_start_date if first_row else "",

					"deduction_amount":
						deduction_amount
						if first_row else "",

					"amount_paid_by_employee_to_gov": 0,

					"paid_amount":
						actual_paid_amount,

					"remaining_amount":
						running_balance,

					"status":
						row.status,

					"remarks":
						row.remarks if first_row else "",

					"additional_salary_date":
						sal_doc.payroll_date
				})

				first_row = False

			# GOVERNMENT PAYMENT ROW
			if gov_paid_amount > 0:

				gov_remaining_balance = (
					running_balance - gov_paid_amount
				)

				if gov_remaining_balance < 0:
					gov_remaining_balance = 0

				final_data.append({
					"parent": "",

					"employee": "",

					"employee_name": "",

					"type_of_penalty": "",

					"deduction_date": "",

					"payroll_start_date": "",

					"deduction_amount": "",

					"amount_paid_by_employee_to_gov":
						gov_paid_amount,

					"paid_amount": 0,

					"remaining_amount":
						gov_remaining_balance,

					"status": row.status,

					"remarks":
						"Paid Directly by Employee to Government",

					"additional_salary_date": ""
				})

				running_balance = gov_remaining_balance

				gov_paid_amount = 0

	return final_data