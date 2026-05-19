# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_link_to_form

class AdditionalDeduction(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.additional_deduction_detail.additional_deduction_detail import AdditionalDeductionDetail

		additional_deduction_detail: DF.Table[AdditionalDeductionDetail]
		amended_from: DF.Link | None
		amount: DF.Currency
		company: DF.Link
		currency: DF.Link
		deduct_full_tax_on_selected_payroll_date: DF.Check
		department: DF.Link | None
		disabled: DF.Check
		employee: DF.Link
		employee_name: DF.Data | None
		from_date: DF.Date | None
		is_recurring: DF.Check
		naming_series: DF.Literal["HR-ADD-.YY.-.MM.-"]
		overwrite_salary_structure_amount: DF.Check
		payroll_date: DF.Date | None
		process_employee_deduction_ref: DF.Data | None
		ref_docname: DF.DynamicLink | None
		ref_doctype: DF.Link | None
		salary_component: DF.Link
		to_date: DF.Date | None
		type: DF.Data | None
	# end: auto-generated types
	pass


	def on_submit(self):
		self.create_additional_salary_from_deduction()
		if self.salary_component == "Total Deduction":
			update_additional_deduction_ref(self)

		
		

	def create_additional_salary_from_deduction(doc):

		# Prevent loop (VERY IMPORTANT)
		if doc.ref_doctype == "Additional Salary":
			return

		# Only for non Total Deduction
		if doc.salary_component == "Total Deduction":
			return

		if not doc.employee:
			return

		# Prevent duplicate
		if frappe.db.exists("Additional Salary", {
			"reference_name": doc.name,
			"reference_doctype": "Additional Deduction",
			"docstatus": 1
		}):
			return

		emp = frappe.get_doc("Employee", doc.employee)

		sal = frappe.new_doc("Additional Salary")

		# -------- Parent --------
		sal.employee = doc.employee
		sal.company = doc.company
		sal.salary_component = doc.salary_component
		sal.payroll_date = doc.payroll_date
		sal.amount = doc.amount

		sal.custom_auto_generated = 1

		# store reverse reference
		sal.ref_doctype = "Additional Deduction"
		sal.ref_docname = doc.name

		sal.insert(ignore_permissions=True)
		sal.submit()

	def on_cancel(self):
		if self.salary_component == "Total Deduction":
			cancel_additional_salary_from_deduction(self)
			remove_additional_deduction_ref(self)
		else:
			return
		
		# 1. REMOVE additional_deduction_ref
		for row in self.additional_deduction_detail or []:

			if not row.employee_deduction_reference:
				continue

			doctype = get_deduction_doctype(row.employee_deduction_reference)

			if not doctype:
				continue

			existing = frappe.db.get_value(
				doctype,
				row.employee_deduction_reference,
				"additional_deduction_ref"
			)

			if not existing:
				continue

			# remove only this AD reference
			updated = remove_reference_link(existing, self.name)

			frappe.db.set_value(
				doctype,
				row.employee_deduction_reference,
				"additional_deduction_ref",
				updated,
				update_modified=False
			)

		
		# 2. CANCEL LINKED ADDITIONAL SALARY
		if self.ref_doctype == "Additional Salary" and self.ref_docname:

			if frappe.db.exists("Additional Salary", self.ref_docname):

				salary_doc = frappe.get_doc("Additional Salary", self.ref_docname)

				if salary_doc.docstatus == 1:
					salary_doc.cancel()

def cancel_additional_salary_from_deduction(self):
	salary_list = frappe.get_all(
		"Additional Salary",
		filters={
			"ref_doctype": "Additional Deduction",
			"ref_docname": self.name
		},
		pluck="name"
	)

	for sal_name in salary_list:

		if not frappe.db.exists("Additional Salary", sal_name):
			continue

		sal_doc = frappe.get_doc("Additional Salary", sal_name)

		# Cancel only if submitted
		if sal_doc.docstatus == 1:
			sal_doc.cancel()

def get_deduction_doctype(reference):

	if frappe.db.exists("Employee Deduction Detail", reference):
		return "Employee Deduction Detail"

	if frappe.db.exists("Outstanding Employee Deduction Detail", reference):
		return "Outstanding Employee Deduction Detail"

	return None

def remove_reference_link(existing_ref, docname):

	if not existing_ref:
		return ""

	refs = [r.strip() for r in existing_ref.split("<br>") if r.strip()]

	cleaned_refs = [r for r in refs if docname not in r]

	return "<br>".join(cleaned_refs)

def update_additional_deduction_ref(self):

	link = get_link_to_form("Additional Deduction", self.name)

	for row in self.additional_deduction_detail or []:

		if not row.employee_deduction_reference:
			continue

		doctype = get_deduction_doctype(row.employee_deduction_reference)

		if not doctype:
			continue

		existing = frappe.db.get_value(
			doctype,
			row.employee_deduction_reference,
			"additional_deduction_ref"
		) or ""

		refs = [r.strip() for r in existing.split("<br>") if r.strip()]

		# remove old incorrect ADA links if any
		refs = [r for r in refs if "additional-salary" not in r]

		if link not in refs:
			refs.append(link)

		updated = "<br>".join(refs)

		frappe.db.set_value(
			doctype,
			row.employee_deduction_reference,
			"additional_deduction_ref",
			updated,
			update_modified=False
		)

		# ALSO update child_ref if Outstanding
		if doctype == "Outstanding Employee Deduction Detail":
			child_ref = frappe.db.get_value(
				doctype,
				row.employee_deduction_reference,
				"child_ref"
			)

			if child_ref:
				frappe.db.set_value(
					"Employee Deduction Detail",
					child_ref,
					"additional_deduction_ref",
					updated,
					update_modified=False
				)

def remove_additional_deduction_ref(self):

	for row in self.additional_deduction_detail or []:

		if not row.employee_deduction_reference:
			continue

		doctype = get_deduction_doctype(row.employee_deduction_reference)
		if not doctype:
			continue

		existing = frappe.db.get_value(
			doctype,
			row.employee_deduction_reference,
			"additional_deduction_ref"
		)

		if not existing:
			continue

		updated = remove_reference_link(existing, self.name)

		frappe.db.set_value(
			doctype,
			row.employee_deduction_reference,
			"additional_deduction_ref",
			updated,
			update_modified=False
		)

		# CASE 1: IF OUTSTANDING → UPDATE CHILD
		if doctype == "Outstanding Employee Deduction Detail":

			child_ref = frappe.db.get_value(
				doctype,
				row.employee_deduction_reference,
				"child_ref"
			)

			if child_ref:
				frappe.db.set_value(
					"Employee Deduction Detail",
					child_ref,
					"additional_deduction_ref",
					updated,
					update_modified=False
				)

		# CASE 2: IF EMPLOYEE DEDUCTION → UPDATE LATEST OUTSTANDING
		if doctype == "Employee Deduction Detail":

			outstanding_rows = frappe.db.sql("""
				SELECT name, additional_deduction_ref
				FROM `tabOutstanding Employee Deduction Detail`
				WHERE child_ref = %s
				OR additional_deduction_ref LIKE %s
				ORDER BY creation DESC
				LIMIT 1
			""", (
				row.name,
				f"%{self.name}%"
			), as_dict=True)

			if outstanding_rows:
				o = outstanding_rows[0]

				if o.additional_deduction_ref:
					updated_out = remove_reference_link(
						o.additional_deduction_ref,
						self.name
					)

					frappe.db.set_value(
						"Outstanding Employee Deduction Detail",
						o.name,
						"additional_deduction_ref",
						updated_out,
						update_modified=False
					)