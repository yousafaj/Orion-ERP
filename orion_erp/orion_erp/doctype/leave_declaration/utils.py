# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def get_employee_active_assets(employee):
	return frappe.db.sql(
		"""
		SELECT ahd.*
		FROM `tabAsset Handover Detail` ahd
		INNER JOIN `tabAsset Handover` ah ON ah.name = ahd.parent
		WHERE ah.employee = %s AND ahd.asset_status != 'Returned'
		ORDER BY ah.creation DESC
		""",
		employee,
		as_dict=True,
	)


def get_employee_outstanding_deductions(employee):
	total = 0

	latest_deduction = frappe.get_all(
		"Employee Deduction",
		filters={"employee": employee, "docstatus": 1},
		fields=["name"],
		order_by="creation desc",
		limit=1,
	)

	if not latest_deduction:
		return total

	ed = frappe.get_doc("Employee Deduction", latest_deduction[0].name)

	for row in ed.employee_deduction_detail or []:
		deduction = flt(row.deduction_amount) or 0
		paid = flt(row.paid_amount) or 0
		remaining = deduction - paid
		if remaining > 0:
			total += remaining

	for row in ed.outstanding_employee_deduction_detail or []:
		deduction = flt(row.deduction_amount) or 0
		paid = flt(row.paid_amount) or 0
		remaining = deduction - paid
		if remaining > 0:
			total += remaining

	return total
