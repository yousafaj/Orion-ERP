"""Bound future annual leave to projected entitlement and existing commitments."""

import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt, getdate
from hrms.hr.doctype.leave_application import leave_application as standard
from orion_erp.orion_erp.services.leave_projection import project_accrual


def uses_projected_balance(leave_type):
    settings = frappe.get_cached_doc("Orion Settings")
    return leave_type in {row.leave_type for row in settings.get("leave_types_for_accrual") or []}


def balance_summary(employee, leave_type, from_date, to_date, application=None, lock=False):
    """Use native ledger/expiry calculations, plus regular future accrual.

    Submitted requests are already in the native ledger balance. Only unsubmitted
    Open/Approved requests are additionally reserved. The request being validated
    is excluded. A row lock serializes competing saves for the same allocation.
    """
    today, start, end = getdate(), getdate(from_date), getdate(to_date)
    allocations = frappe.get_all(
        "Leave Allocation",
        filters={"employee": employee, "leave_type": leave_type, "docstatus": 1,
                 "from_date": ["<=", start], "to_date": [">=", end]},
        fields=["name", "from_date", "to_date"], order_by="from_date desc",
    )
    if len(allocations) != 1:
        frappe.throw(_("A single submitted leave allocation must cover this request. Ask HR to check the allocation dates; split requests that cross allocation periods."))
    allocation = allocations[0]
    if lock:
        frappe.db.sql("SELECT name FROM `tabLeave Allocation` WHERE name = %s FOR UPDATE", allocation.name)

    native = standard.get_leave_balance_on(
        employee, leave_type, start, end,
        consider_all_leaves_in_the_allocation_period=True, for_consumption=True,
    )
    current = standard.get_leave_balance_on(employee, leave_type, today, today)
    # A submitted request already has its own debit. Do not charge it twice on
    # subsequent validation (including permitted attachment updates).
    own_debit = 0.0
    if application:
        entries = frappe.get_all(
            "Leave Ledger Entry", filters={"employee": employee, "leave_type": leave_type,
                "transaction_type": "Leave Application", "transaction_name": application,
                "docstatus": 1}, fields=["leaves"],
        )
        own_debit = -sum(flt(row.leaves) for row in entries)

    pending = frappe.get_all(
        "Leave Application", filters={"employee": employee, "leave_type": leave_type,
            "docstatus": 0, "status": ["in", ["Open", "Approved"]],
            "from_date": ["<=", allocation.to_date], "to_date": [">=", allocation.from_date]},
        fields=["name", "total_leave_days", "workflow_state", "custom_approval_status"],
    )
    reserved = sum(flt(row.total_leave_days) for row in pending
                   if row.name != application
                   and row.workflow_state not in ("Rejected", "Cancelled")
                   and row.custom_approval_status not in ("Rejected", "Cancelled"))
    leave_doc = frappe.get_cached_doc("Leave Type", leave_type)
    joining = getdate(frappe.db.get_value("Employee", employee, "date_of_joining"))
    rules = [dict(from_months=cint(row.from_months), to_months=cint(row.to_months),
                  days_per_month=flt(row.days_per_month))
             for row in leave_doc.get("custom_annual_leave_accrual_rules") or []]
    forecast = project_accrual(joining, today, start, rules,
                              getdate(allocation.from_date), getdate(allocation.to_date))
    # Preserve native expiry/carry-forward restrictions. Regular new credits are
    # usable up to allocation expiry; expiring carry-forward remains native.
    available = min(flt(native.get("leave_balance_for_consumption")) + own_debit + forecast - reserved,
                    date_diff(allocation.to_date, start) + 1)
    return frappe._dict(current_balance=flt(current, 2), projected_accrual=forecast,
                        pending_reserved=flt(reserved, 2), projected_balance=flt(available, 2))


class OrionLeaveApplication(standard.LeaveApplication):
    def validate_balance_leaves(self):
        if not self.leave_type or not uses_projected_balance(self.leave_type):
            return super().validate_balance_leaves()
        if self.status in ("Rejected", "Cancelled") or self.docstatus == 2:
            return
        if not self.from_date or not self.to_date:
            return
        self.total_leave_days = standard.get_number_of_leave_days(
            self.employee, self.leave_type, self.from_date, self.to_date,
            self.half_day, self.half_day_date,
        )
        if self.total_leave_days <= 0:
            frappe.throw(_("The selected dates contain no chargeable leave days."))
        summary = balance_summary(self.employee, self.leave_type, self.from_date,
                                  self.to_date, self.name, lock=True)
        self.custom_current_leave_balance = summary.current_balance
        self.custom_projected_leave_accrual = summary.projected_accrual
        self.custom_pending_leave_reserved = summary.pending_reserved
        self.leave_balance = summary.projected_balance
        self.custom_leave_balance_after = flt(summary.projected_balance - self.total_leave_days, 2)
        if self.status not in ("Rejected", "Cancelled") and self.docstatus != 2:
            if flt(self.total_leave_days, 2) > summary.projected_balance:
                frappe.throw(_("Insufficient projected leave balance on {0}: {1} days available, {2} days requested. Pending requests reserve {3} days.").format(
                    self.from_date, summary.projected_balance, self.total_leave_days, summary.pending_reserved),
                    exc=standard.InsufficientLeaveBalanceError, title=_("Insufficient Leave Balance"))


@frappe.whitelist()
def get_projected_leave_balance(employee, leave_type, from_date, to_date, application=None):
    standard.validate_leave_access(employee)
    if not uses_projected_balance(leave_type):
        return None
    if application and frappe.db.exists("Leave Application", application):
        doc = frappe.get_doc("Leave Application", application)
        doc.check_permission("read")
        if doc.employee != employee or doc.leave_type != leave_type:
            frappe.throw(_("Leave application does not match the employee and leave type."))
    else:
        application = None
    return balance_summary(employee, leave_type, from_date, to_date, application)
