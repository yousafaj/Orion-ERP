"""Bound future annual leave to projected entitlement and existing commitments."""

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, flt, getdate
from hrms.hr.doctype.leave_application import leave_application as standard
from orion_erp.orion_erp.services.leave_projection import anniversary, completed_months, project_accrual


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
    if not allocations and start > today:
        return next_year_balance(employee, leave_type, start, end, application, lock)
    if len(allocations) != 1:
        frappe.throw(_("A single submitted leave allocation must cover this request. Ask HR to check the allocation dates; split requests that cross allocation periods."))
    allocation = allocations[0]
    if lock:
        frappe.db.sql("SELECT name FROM `tabLeave Allocation` WHERE name = %s FOR UPDATE", allocation.name)

    native = standard.get_leave_balance_on(
        employee, leave_type, start, end,
        consider_all_leaves_in_the_allocation_period=True, for_consumption=True,
    )
    # Reserve commitments before the final allocation-calendar cap. Subtracting
    # pending days from an already capped balance falsely rejects valid requests
    # near expiry. Preserve the native separate carry-forward expiry cap.
    eligible = flt(native.get("leave_balance"))
    native_allocation = standard.get_leave_allocation_records(employee, start, leave_type).get(leave_type)
    if native_allocation and native_allocation.unused_leaves:
        cf_expiry = standard.get_allocation_expiry_for_cf_leaves(
            employee, leave_type, end, native_allocation.from_date)
        if cf_expiry and start <= getdate(cf_expiry):
            cf_taken = standard.get_new_and_cf_leaves_taken(native_allocation, cf_expiry)[1]
            cf_remaining = max(0, flt(native_allocation.unused_leaves) + flt(cf_taken))
            eligible -= cf_remaining - min(cf_remaining, date_diff(cf_expiry, start) + 1)
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
    available = min(eligible + own_debit + forecast - reserved,
                    date_diff(allocation.to_date, start) + 1)
    return frappe._dict(current_balance=flt(current, 2), projected_accrual=forecast,
                        pending_reserved=flt(reserved, 2), projected_balance=flt(available, 2))


def next_year_balance(employee, leave_type, start, end, application=None, lock=False):
    """Forecast the next service year without pre-posting credits or carry-forward.

    An existing current allocation establishes entitlement. Preserve its expiry,
    configured carry-forward ceiling and commitments in both years. The final
    completed service month's credit belongs to the closing year, even though
    it is posted on the first day of the following year.
    """
    today = getdate()
    current = frappe.get_all("Leave Allocation",
        filters={"employee": employee, "leave_type": leave_type, "docstatus": 1,
                 "from_date": ["<=", today], "to_date": [">=", today]},
        fields=["name", "from_date", "to_date"])
    if len(current) != 1:
        frappe.throw(_("No current annual leave entitlement is available. Ask HR to check the employee's allocation."))
    source = current[0]
    joining = getdate(frappe.db.get_value("Employee", employee, "date_of_joining"))
    next_start = getdate(add_days(source.to_date, 1))
    month = completed_months(joining, next_start)
    next_end = getdate(add_days(anniversary(joining, month + 12), -1))
    if month < 12 or month % 12 or anniversary(joining, month) != next_start or not (next_start <= start <= end <= next_end):
        frappe.throw(_("The requested dates are outside the next annual leave year. Ask HR to check the allocation dates."))
    existing = frappe.get_all("Leave Allocation",
        filters={"employee": employee, "leave_type": leave_type, "docstatus": 1,
                 "from_date": ["<=", next_end], "to_date": [">=", next_start]}, fields=["name"])
    if existing:
        frappe.throw(_("An allocation already exists in the requested year but does not cover the selected dates. Ask HR to check its dates."))
    if lock:
        frappe.db.sql("SELECT name FROM `tabLeave Allocation` WHERE name=%s FOR UPDATE", source.name)
    leave_doc = frappe.get_cached_doc("Leave Type", leave_type)
    rules = [dict(from_months=cint(r.from_months), to_months=cint(r.to_months), days_per_month=flt(r.days_per_month))
             for r in leave_doc.get("custom_annual_leave_accrual_rules") or []]
    closing = balance_summary(employee, leave_type, source.to_date, source.to_date, application)
    # Recalculate raw closing entitlement: the native calendar cap would reduce
    # a year-end snapshot to one day, which is not the carry-forward balance.
    raw = standard.get_leave_balance_on(employee, leave_type, source.to_date, source.to_date,
        consider_all_leaves_in_the_allocation_period=True, for_consumption=True)
    closing_credit = project_accrual(joining, today, next_start, rules, getdate(source.from_date), next_start)
    own = 0.0
    if application:
        entries = frappe.get_all("Leave Ledger Entry", filters={"transaction_type": "Leave Application",
            "transaction_name": application, "employee": employee, "leave_type": leave_type, "docstatus": 1},
            fields=["leaves", "from_date", "to_date"])
        own = -sum(flt(r.leaves) for r in entries
                   if getdate(r.from_date) >= next_start and getdate(r.to_date) <= next_end)
    carry_limit = flt(leave_doc.maximum_carry_forwarded_leaves)
    carry = min(max(0, flt(raw.get("leave_balance")) + closing_credit - closing.pending_reserved), carry_limit) if leave_doc.is_carry_forward else 0.0
    expiry_days = cint(leave_doc.expire_carry_forwarded_leaves_after_days)
    if expiry_days:
        expiry = getdate(add_days(next_start, expiry_days - 1))
        carry = 0.0 if start > expiry else min(carry, date_diff(expiry, start) + 1)
    credit = project_accrual(joining, next_start, start, rules, next_start, next_end)
    taken = flt(standard.get_leaves_for_period(employee, leave_type, next_start, next_end))
    pending = frappe.get_all("Leave Application", filters={"employee": employee, "leave_type": leave_type,
        "docstatus": 0, "status": ["in", ["Open", "Approved"]],
        "from_date": ["<=", next_end], "to_date": [">=", next_start]},
        fields=["name", "total_leave_days", "workflow_state", "custom_approval_status"])
    reserved = sum(flt(r.total_leave_days) for r in pending if r.name != application
        and r.workflow_state not in ("Rejected", "Cancelled") and r.custom_approval_status not in ("Rejected", "Cancelled"))
    available = min(carry + credit + taken + own - reserved, date_diff(next_end, start) + 1)
    return frappe._dict(current_balance=closing.current_balance, projected_accrual=flt(closing_credit + credit, 2),
        pending_reserved=flt(reserved, 2), projected_balance=flt(available, 2),
        projected_carry_forward=flt(carry, 2), carry_forward_limit=carry_limit)


class OrionLeaveApplication(standard.LeaveApplication):
    def validate_dates_across_allocation(self):
        if uses_projected_balance(self.leave_type):
            # The projected validator checks current or next-year entitlement.
            # Native date, half-day and backdated-access checks still run.
            return
        return super().validate_dates_across_allocation()

    def validate_balance_leaves(self):
        if not self.leave_type or not uses_projected_balance(self.leave_type):
            return super().validate_balance_leaves()
        if self.docstatus == 2:
            return
        if not self.is_new():
            # Orion records rejection/cancellation in active approver fields
            # during save. These transitions must remain possible even when
            # entitlement has subsequently decreased. Approval permissions are
            # still enforced by validate_leave_approval.
            from orion_erp.orion_erp.validations.leave_application import get_approval_flow
            terminating = any(self.get(row["approver_field"])
                              and self.get(row["status_field"]) in ("Rejected", "Cancelled")
                              for row in get_approval_flow(self))
            if self.status in ("Rejected", "Cancelled") or terminating:
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
        if self.is_new() or self.status not in ("Rejected", "Cancelled"):
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
