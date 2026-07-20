# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from orion_erp.orion_erp.services.additional_deduction import (
    cancel_additional_salary_from_deduction,
    update_additional_deduction_ref,
    remove_additional_deduction_ref,
)
from orion_erp.orion_erp.services.utils import get_deduction_doctype, remove_reference_link


class AdditionalDeduction(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from orion_erp.orion_erp.doctype.additional_deduction_detail.additional_deduction_detail import AdditionalDeductionDetail

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

    def on_submit(self):
        self.create_additional_salary_from_deduction()
        if self.salary_component == "Total Deduction":
            update_additional_deduction_ref(self)

    def create_additional_salary_from_deduction(doc):
        if doc.ref_doctype == "Additional Salary":
            return
        if doc.salary_component == "Total Deduction":
            return
        if not doc.employee:
            return

        if frappe.db.exists("Additional Salary", {
            "reference_name": doc.name,
            "reference_doctype": "Additional Deduction",
            "docstatus": 1
        }):
            return

        sal = frappe.new_doc("Additional Salary")
        sal.employee = doc.employee
        sal.company = doc.company
        sal.salary_component = doc.salary_component
        sal.payroll_date = doc.payroll_date
        sal.amount = doc.amount
        sal.custom_auto_generated = 1
        sal.ref_doctype = "Additional Deduction"
        sal.ref_docname = doc.name
        sal.insert(ignore_permissions=True)
        sal.submit()

    def on_cancel(self):
        if self.salary_component == "Total Deduction":
            cancel_additional_salary_from_deduction(self)
            remove_additional_deduction_ref(self)

            for row in self.additional_deduction_detail or []:
                if not row.employee_deduction_reference:
                    continue
                doctype = get_deduction_doctype(row.employee_deduction_reference)
                if not doctype:
                    continue
                existing = frappe.db.get_value(
                    doctype, row.employee_deduction_reference, "additional_deduction_ref"
                )
                if not existing:
                    continue
                updated = remove_reference_link(existing, self.name)
                frappe.db.set_value(
                    doctype, row.employee_deduction_reference,
                    "additional_deduction_ref", updated,
                    update_modified=False
                )

            if self.ref_doctype == "Additional Salary" and self.ref_docname:
                if frappe.db.exists("Additional Salary", self.ref_docname):
                    salary_doc = frappe.get_doc("Additional Salary", self.ref_docname)
                    if salary_doc.docstatus == 1:
                        salary_doc.cancel()
