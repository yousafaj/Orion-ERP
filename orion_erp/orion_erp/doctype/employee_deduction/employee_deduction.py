# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import re

from orion_erp.orion_erp.services.employee_deduction import (
    validate_installment_amount,
    get_outstanding_penalties,
    run_deduction_manual,
    run_deduction_cron,
    process_deductions,
    create_deduction_additional_salary,
    sync_to_outstanding,
    validate_payroll_dates,
)


class EmployeeDeduction(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from orion_erp.orion_erp.doctype.employee_deduction_detail.employee_deduction_detail import EmployeeDeductionDetail
        from orion_erp.orion_erp.doctype.outstanding_employee_deduction_detail.outstanding_employee_deduction_detail import OutstandingEmployeeDeductionDetail

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

    def on_cancel(self):
        invalid_refs = []
        all_rows = (self.employee_deduction_detail or []) + (self.outstanding_employee_deduction_detail or [])

        for row in all_rows:
            if row.additional_deduction_ref:
                refs = re.findall(r'>([^<]+)<', row.additional_deduction_ref)
                for ref in refs:
                    if frappe.db.get_value("Additional Deduction", ref, "docstatus") == 1:
                        invalid_refs.append(ref)

        if invalid_refs:
            frappe.throw(
                "Please cancel the following Additional Deduction document(s) first:<br><b>"
                + "<br>".join(set(invalid_refs)) +
                "</b>"
            )

    def validate(self):
        self.update_child_payment()
        self.update_parent_totals()
        validate_installment_amount(self)
        validate_payroll_dates(self)

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

    def update_child_payment(self):
        all_rows = (self.employee_deduction_detail or []) + (self.outstanding_employee_deduction_detail or [])
        for row in all_rows:
            row.deduction_amount = row.deduction_amount or 0
            row.paid_amount = row.paid_amount or 0

            if row.paid and row.partial_paid:
                frappe.throw(f"Row {row.idx}: Cannot select both Paid and Partial Paid")

            if row.paid:
                self._apply_full_payment(row)
            elif row.partial_paid:
                self._apply_partial_payment(row)
            else:
                self._recalculate_status(row)

            if abs(row.remaining_amount) < 0.001:
                row.remaining_amount = 0

            if row.doctype == "Employee Deduction Detail":
                sync_to_outstanding(self, row)

    def _apply_full_payment(self, row):
        row.paid_amount = row.deduction_amount
        row.remaining_amount = 0
        row.status = "Paid"

    def _apply_partial_payment(self, row):
        if not row.partial_paid_amount or row.partial_paid_amount <= 0:
            frappe.throw(f"Row {row.idx}: Enter partial paid amount")
        if row.partial_paid_amount > row.remaining_amount:
            frappe.throw(f"Row {row.idx}: Partial amount exceeds remaining")

        row.paid_amount = min(row.deduction_amount, (row.paid_amount or 0) + row.partial_paid_amount)
        row.amount_paid_by_employee_to_gov = min(
            row.deduction_amount,
            (row.amount_paid_by_employee_to_gov or 0) + row.partial_paid_amount
        )
        row.remaining_amount = row.deduction_amount - row.paid_amount
        row.status = "Paid" if row.remaining_amount == 0 else "Partial Paid"
        row.partial_paid_amount = 0
        row.partial_paid = 0

    def _recalculate_status(self, row):
        row.remaining_amount = row.deduction_amount - row.paid_amount
        if row.paid_amount == 0:
            row.status = "Unpaid"
        elif row.remaining_amount == 0:
            row.status = "Paid"
        else:
            row.status = "Partial Paid"

    def update_parent_totals(self):
        total = paid = remaining = total_rows = paid_rows = unpaid_rows = 0

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

        if total_rows == 0:
            self.status = "Draft"
        elif paid_rows == total_rows:
            self.status = "Paid"
        elif unpaid_rows == total_rows:
            self.status = "Unpaid"
        else:
            self.status = "Partial Paid"
