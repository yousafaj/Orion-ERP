# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from orion_erp.orion_erp.doctype.leave_declaration.utils import (
	get_employee_active_assets,
	get_employee_outstanding_deductions,
)


@frappe.whitelist()
def get_leave_balance(employee, leave_type, date):
	from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
	return get_leave_balance_on(employee, leave_type, date)


@frappe.whitelist()
def get_employee_asset_details(employee):
	return get_employee_active_assets(employee)


@frappe.whitelist()
def get_leave_application_data(leave_application):
	la = frappe.get_doc("Leave Application", leave_application)
	emp = frappe.get_cached_doc("Employee", la.employee)
	passport = frappe.db.get_value(
		"Employee cdt",
		{
			"parent": la.employee,
			"certification_name": "Passport no",
		},
		"reference_no",
	)

	return {
		"employee": la.employee,
		"employee_name": la.employee_name,
		"company": la.company,
		"leave_type": la.leave_type,
		"leave_start_date": la.from_date,
		"leave_end_date": la.to_date,
		"leaving_date": la.from_date,
		"designation": emp.designation,
		"passport_number": passport,
		"total_leave_days": la.total_leave_days,
	}


@frappe.whitelist()
def get_available_leave_applications(doctype, txt, searchfield, start, page_length, filters):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)

	filters = filters or {}
	employee = filters.get("employee")

	unpaid_types = frappe.get_all("Leave Type", filters={"is_lwp": 1}, pluck="name")

	from frappe.query_builder import DocType

	LA = DocType("Leave Application")

	query = (
		frappe.qb.from_(LA)
		.select(LA.name, LA.employee_name, LA.leave_type, LA.from_date, LA.to_date)
		.where(LA.docstatus == 1)
		.where(LA.custom_approval_status == "Approved")
		.where(LA.custom_leave_declaration.isnull())
		.orderby(LA.from_date, order=frappe.qb.desc)
	)

	if unpaid_types:
		query = query.where(LA.leave_type.notin(unpaid_types))
	if employee:
		query = query.where(LA.employee == employee)
	if txt:
		search_term = f"%{txt}%"
		query = query.where(
			(LA.name.like(search_term))
			| (LA.employee_name.like(search_term))
			| (LA.leave_type.like(search_term))
		)

	apps = query.run(as_dict=True)
	return [[a.name, a.employee_name or "", a.leave_type or "", str(a.from_date) if a.from_date else "", str(a.to_date) if a.to_date else ""] for a in apps]


@frappe.whitelist()
def get_passport_number(employee):
	passport = frappe.db.get_value(
		"Employee cdt",
		{
			"parent": employee,
			"certification_name": "Passport no",
		},
		"reference_no",
	)
	return passport


@frappe.whitelist()
def get_outstanding_advance(employee):
	return get_employee_outstanding_deductions(employee)
