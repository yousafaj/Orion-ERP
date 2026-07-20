# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from orion_erp.orion_erp.services.process_employee_deductions import (
    validate_duplicate_transaction,
    populate_outstanding_installments,
    fetch_new_deductions,
    get_new_deductions_for_process,
    process_create_additional_salary,
    validate_salary_slip_before_cancel,
    validate_salary_slip_exists,
    cancel_linked_additional_deductions,
)


class ProcessEmployeeDeductions(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from orion_erp.orion_erp.doctype.process_employee_deduction_detail.process_employee_deduction_detail import ProcessEmployeeDeductionDetail

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
            if self.docstatus == 0:
                fetch_new_deductions(self)
            return
        populate_outstanding_installments(self)

    def on_submit(self):
        validate_salary_slip_exists(self)
        process_create_additional_salary(self)

    def on_cancel(self):
        validate_salary_slip_before_cancel(self)
        cancel_linked_additional_deductions(self)
