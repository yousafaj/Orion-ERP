# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from orion_erp.orion_erp.services.leave_settlement import (
    get_leave_pay_data,
    get_ticket_allowance,
    mark_ticket_paid,
    revert_ticket_paid,
    validate_ticket_allowance,
    create_leave_settlement_deduction,
    create_ticket_allowance_additional_salary,
    cancel_linked_ticket_allowance_additional_salary,
    create_leave_encashment_for_settlement,
    cancel_linked_leave_encashments,
    cancel_linked_additional_deductions,
    validate_salary_slip_before_cancel,
    get_leave_period,
)


class LeaveSettlement(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from orion_erp.orion_erp.doctype.gratuity_pay.gratuity_pay import GratuityPay
        from orion_erp.orion_erp.doctype.leave_pay.leave_pay import LeavePay
        from orion_erp.orion_erp.doctype.leave_settlement_deductions.leave_settlement_deductions import LeaveSettlementDeductions
        from orion_erp.orion_erp.doctype.salary_due.salary_due import SalaryDue
        from orion_erp.orion_erp.doctype.ticket_allowance.ticket_allowance import TicketAllowance

        adjustments_if_any: DF.Currency
        amended_from: DF.Link | None
        company: DF.Link
        date_of_settlement: DF.Date
        department: DF.Link | None
        doj__re_joining_date: DF.Date | None
        employee: DF.Link
        employee_name: DF.Data | None
        gratuity_pay: DF.Table[GratuityPay]
        last_working_day: DF.Date | None
        leave_pay: DF.Table[LeavePay]
        leave_settlement_deductions: DF.Table[LeaveSettlementDeductions]
        monthly_salary: DF.Currency
        other_allowance: DF.Currency
        other_deduction: DF.Currency
        outstanding_advance: DF.Currency
        overtime_allowance: DF.Currency
        position: DF.Link | None
        posting_date: DF.Date | None
        remark: DF.LongText | None
        salary_due: DF.Table[SalaryDue]
        ticket_allowance: DF.Table[TicketAllowance]
        total_deductions: DF.Currency
        total_entitlements: DF.Currency
        total_service: DF.Data | None
        total_settlement_payable: DF.Currency
        traffic_fine: DF.Currency
        type_of_settlement: DF.Literal["", "Vacation Settlement", "Final Settlement", "Labour Court Settlement", "Internal Transfer Settlement"]
    # end: auto-generated types

    @frappe.whitelist()
    def populate_leave_settlement_deductions(self):
        self.leave_settlement_deductions = []
        if not self.employee:
            return

        parent = frappe.get_all(
            "Employee Deduction",
            filters={"employee": self.employee, "docstatus": 1},
            fields=["name"],
            order_by="creation desc",
            limit=1
        )
        if not parent:
            return

        doc = frappe.get_doc("Employee Deduction", parent[0].name)
        self._append_deduction_rows(doc, doc.employee_deduction_detail)
        self._append_deduction_rows(doc, doc.outstanding_employee_deduction_detail)

    def _append_deduction_rows(self, doc, rows):
        for row in rows or []:
            if flt(row.remaining_amount) <= 0:
                continue
            self.append("leave_settlement_deductions", {
                "employee": doc.employee,
                "employee_name": doc.employee_name,
                "type_of_penalty": row.type_of_penalty,
                "date_of_deduction_occurred": row.deduction_date,
                "outstanding_amount": row.remaining_amount,
                "installment_amount": flt(row.remaining_amount),
                "employee_deduction_reference": row.name,
                "employee_deduction_parent_reference": row.parent,
                "amount_to_be_deducted_this_month": flt(row.remaining_amount)
            })

    def on_submit(self):
        mark_ticket_paid(self)
        create_leave_settlement_deduction(self)
        create_ticket_allowance_additional_salary(self)
        create_leave_encashment_for_settlement(self)

    def validate(self):
        validate_ticket_allowance(self)

    def on_cancel(self):
        validate_salary_slip_before_cancel(self)
        cancel_linked_additional_deductions(self)
        cancel_linked_ticket_allowance_additional_salary(self)
        cancel_linked_leave_encashments(self)
        revert_ticket_paid(self)
