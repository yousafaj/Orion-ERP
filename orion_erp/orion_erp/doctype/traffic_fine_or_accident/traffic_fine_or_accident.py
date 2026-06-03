# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from orion_erp.orion_erp.doctype.monthly_billing.monthly_billing import rental_on_date


class TrafficFineorAccident(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from orion_erp.orion_erp.doctype.accident_logs.accident_logs import AccidentLogs
        from orion_erp.orion_erp.doctype.fines_cdt.fines_cdt import Finescdt

        accident_detail: DF.Table[AccidentLogs]
        amended_from: DF.Link | None
        closing_status: DF.Literal["", "Paid by Client", "Paid by Driver", "Paid by Company"]
        customer: DF.Link | None
        date: DF.Date
        detail: DF.Table[Finescdt]
        driver: DF.Link | None
        employee_deduction: DF.Link | None
        employment_type: DF.Link | None
        evidence: DF.Attach | None
        fine_status: DF.Literal["", "Faulty", "Not Faulty"]
        post_fine: DF.Check
        project: DF.Link | None
        shift: DF.Link | None
        status: DF.Literal["", "Open", "Closed"]
        total_amount: DF.Currency
        vehicle: DF.Link | None
        vehicle_type: DF.Data | None
    # end: auto-generated types

    def validate(self):
        self._set_customer_from_rental()
        # Sum the recorded amounts (fines + accident costs) for billing/deduction.
        self.total_amount = sum(flt(r.amount) for r in (self.detail or [])) + sum(
            flt(r.amount) for r in (self.accident_detail or [])
        )

    def _set_customer_from_rental(self):
        """Auto-fill Customer (the company the fine belongs to) from the rental
        active on this date, so it's shown directly without opening the Project.
        Leaves a manually-set customer alone."""
        if self.customer or not (self.vehicle and self.date):
            return
        rental = rental_on_date(self.vehicle, self.date)
        if rental:
            self.customer = rental.customer
            self.project = rental.project_to

    def on_submit(self):
        # Operations records the fine with evidence and submits; Accounts assign
        # Responsibility (closing_status) afterwards. Status stays Open until then.
        if not self.evidence:
            frappe.throw(_("You must attach Evidence before submitting this document."))

    def on_update_after_submit(self):
        # Once Accounts set Responsibility, mark the record Closed.
        if self.closing_status and self.status != "Closed":
            self.db_set("status", "Closed", update_modified=True)


@frappe.whitelist()
def create_employee_deduction(name):
    """Accounts-only: for a Driver-responsible fine/accident, create a DRAFT
    Employee Deduction shell for the driver's employee. Accounts then add the
    penalty installment rows (with the amount shown in remarks) and submit."""
    frappe.only_for(("Accounts Manager", "System Manager"))
    doc = frappe.get_doc("Traffic Fine or Accident", name)

    if doc.closing_status != "Paid by Driver":
        frappe.throw(_("Employee deduction applies only when Responsibility is 'Paid by Driver'."))
    if doc.employee_deduction:
        frappe.throw(
            _("An Employee Deduction already exists for this record: {0}").format(doc.employee_deduction)
        )
    if not doc.driver:
        frappe.throw(_("Set the Driver before creating an employee deduction."))

    employee = frappe.db.get_value("Driver", doc.driver, "employee")
    if not employee:
        frappe.throw(_("Driver {0} has no linked Employee.").format(doc.driver))
    employee_name = frappe.db.get_value("Employee", employee, "employee_name")

    deduction = frappe.get_doc(
        {
            "doctype": "Employee Deduction",
            "naming_series": "EMP-DED-.YYYY.-",
            "employee": employee,
            "employee_name": employee_name,
            "transaction_date": doc.date,
            "remarks": _(
                "Traffic Fine / Accident {0} — Vehicle {1} — Amount AED {2}. "
                "Add penalty installment row(s) and submit."
            ).format(doc.name, doc.vehicle or "-", flt(doc.total_amount)),
        }
    )
    deduction.insert(ignore_permissions=True)
    doc.db_set("employee_deduction", deduction.name, update_modified=True)
    return deduction.name
