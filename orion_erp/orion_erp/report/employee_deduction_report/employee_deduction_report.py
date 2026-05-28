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

	return [
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
			"label": "Paid Amount",
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"label": "Amount Paid By Employee to Gov",
			"fieldname": "amount_paid_by_employee_to_gov",
			"fieldtype": "Currency",
			"width": 220
		},
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
			"label": "Additional Deduction",
			"fieldname": "additional_deduction_ref",
			"fieldtype": "Link",
			"options": "Additional Deduction",
			"width": 200
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
	]


def get_data(filters):

	filters = filters or {}

	conditions = ""
	values = {}

	if filters.get("employee"):
		conditions += "AND ed.employee = %(employee)s"
		values["employee"] = filters.get("employee")

	if filters.get("status"):
		conditions += "AND edd.status = %(status)s"
		values["status"] = filters.get("status")

	if filters.get("penalty_type"):
		conditions += "AND edd.type_of_penalty = %(penalty_type)s"
		values["penalty_type"] = filters.get("penalty_type")

	if filters.get("deduction_date"):
		conditions += "AND edd.deduction_date >= %(deduction_date)s"
		values["deduction_date"] = filters.get("deduction_date")

	if filters.get("payroll_start_date"):
		conditions += "AND edd.payroll_start_date >= %(payroll_start_date)s"
		values["payroll_start_date"] = filters.get("payroll_start_date")

	if filters.get("payroll_end_date"):
		conditions += "AND edd.payroll_start_date <= %(payroll_end_date)s"
		values["payroll_end_date"] = filters.get("payroll_end_date")

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
			edd.paid_amount as raw_paid_amount,
			edd.amount_paid_by_employee_to_gov,
			edd.remaining_amount as raw_remaining_amount,
			edd.status,
			edd.remarks,
			edd.reference,
			edd.additional_deduction_ref
		FROM `tabEmployee Deduction Detail` edd
		INNER JOIN `tabEmployee Deduction` ed
			ON ed.name = edd.parent
		WHERE ed.docstatus = 1
		{conditions}
		ORDER BY ed.employee, edd.deduction_date, edd.name
		""",
		values,
		as_dict=1
	)

	final_data = []
	seen_edd = set()
	total_deduction_amount = 0
	total_paid_amount = 0
	total_gov_paid = 0
	total_remaining = 0

	for row in data:

		deduction_amount = row.get("deduction_amount") or 0
		gov_paid_amount = row.get("amount_paid_by_employee_to_gov") or 0
		remaining = row.get("raw_remaining_amount") or 0
		edd_name = row.get("edd_name")

		additional_deduction_names = []
		if row.get("additional_deduction_ref"):
			additional_deduction_names = re.findall(
				r'>([^<]+)<',
				row.get("additional_deduction_ref")
			)

		if not additional_deduction_names:
			final_data.append({
				"parent": row.parent,
				"employee": row.employee,
				"employee_name": row.employee_name,
				"type_of_penalty": row.type_of_penalty,
				"deduction_date": row.deduction_date,
				"payroll_start_date": row.payroll_start_date,
				"deduction_amount": deduction_amount,
				"paid_amount": 0,
				"amount_paid_by_employee_to_gov": gov_paid_amount,
				"remaining_amount": remaining,
				"status": row.status,
				"additional_deduction_ref": "",
				"additional_salary_date": None,
				"remarks": row.remarks
			})
			if edd_name not in seen_edd:
				seen_edd.add(edd_name)
				total_deduction_amount += deduction_amount
				total_gov_paid += gov_paid_amount
				total_remaining += remaining
			continue

		for ad_name in additional_deduction_names:
			try:
				ad_doc = frappe.get_doc("Additional Deduction", ad_name)
			except Exception:
				continue

			paid = 0
			for d in ad_doc.additional_deduction_detail or []:
				if d.employee_deduction_reference == row.edd_name:
					paid += d.installation_amount or 0

			total_paid_amount += paid

			final_data.append({
				"parent": row.parent,
				"employee": row.employee,
				"employee_name": row.employee_name,
				"type_of_penalty": row.type_of_penalty,
				"deduction_date": row.deduction_date,
				"payroll_start_date": row.payroll_start_date,
				"deduction_amount": deduction_amount,
				"paid_amount": paid,
				"amount_paid_by_employee_to_gov": gov_paid_amount,
				"remaining_amount": remaining,
				"status": row.status,
				"additional_deduction_ref": ad_name,
				"additional_salary_date": ad_doc.payroll_date,
				"remarks": row.remarks
			})

		if edd_name not in seen_edd:
			seen_edd.add(edd_name)
			total_deduction_amount += deduction_amount
			total_gov_paid += gov_paid_amount
			total_remaining += remaining

	final_data.append({
		"parent": "Total",
		"employee": "",
		"employee_name": "",
		"type_of_penalty": "",
		"deduction_date": None,
		"payroll_start_date": None,
		"deduction_amount": total_deduction_amount,
		"paid_amount": total_paid_amount,
		"amount_paid_by_employee_to_gov": total_gov_paid,
		"remaining_amount": total_remaining,
		"status": "",
		"additional_deduction_ref": "",
		"additional_salary_date": None,
		"remarks": ""
	})

	return final_data
