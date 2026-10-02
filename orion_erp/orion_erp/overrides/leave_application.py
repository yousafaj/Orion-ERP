"""Bound future annual leave to projected entitlement and existing commitments."""

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, flt, getdate
from hrms.hr.doctype.leave_application import leave_application as standard
from orion_erp.orion_erp.services.leave_projection import anniversary, completed_months, project_accrual


def uses_projected_balance(leave_type):
    settings = frappe.get_cached_doc("Orion Settings")
    return leave_type in {row.leave_type for row in settings.get("leave_types_for_accrual") or []}


def days_in_period(employee, leave_type, row, period_start, period_end):
    """Clip a commitment before counting holidays and its single half-day."""
    start = max(getdate(row.from_date), getdate(period_start))
    end = min(getdate(row.to_date), getdate(period_end))
    if start > end:
        return 0.0
    half_date = getdate(row.half_day_date) if row.half_day_date else None
    half = cint(row.half_day) and (
        (half_date and start <= half_date <= end)
        or (not half_date and getdate(row.from_date) == getdate(row.to_date)))
    return max(0, flt(standard.get_number_of_leave_days(
        employee, leave_type, start, end, int(bool(half)), half_date,
        holiday_list=row.holiday_list)))


def pending_in_period(employee, leave_type, start, end, application=None):
    pending = frappe.get_all("Leave Application", filters={
        "employee": employee, "leave_type": leave_type, "docstatus": 0,
        "status": ["in", ["Open", "Approved"]],
        "from_date": ["<=", end], "to_date": [">=", start]},
        fields=["name", "from_date", "to_date", "half_day", "half_day_date",
                "workflow_state", "custom_approval_status"])
    return sum(days_in_period(employee, leave_type, row, start, end)
               for row in pending if row.name != application
               and row.workflow_state not in ("Rejected", "Cancelled")
               and row.custom_approval_status not in ("Rejected", "Cancelled"))


def own_debit_in_period(employee, leave_type, application, start, end,
                        half_day=0, half_day_date=None):
    if not application:
        return 0.0
    entries = frappe.get_all("Leave Ledger Entry", filters={
        "employee": employee, "leave_type": leave_type,
        "transaction_type": "Leave Application", "transaction_name": application,
        "docstatus": 1}, fields=["leaves", "from_date", "to_date", "holiday_list"])
    total = 0.0
    for row in entries:
        if getdate(row.from_date) >= getdate(start) and getdate(row.to_date) <= getdate(end):
            total -= flt(row.leaves)
        else:
            row.half_day, row.half_day_date = half_day, half_day_date
            total += days_in_period(employee, leave_type, row, start, end)
    return total


def balance_summary(employee, leave_type, from_date, to_date, application=None, lock=False,
                    half_day=0, half_day_date=None):
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
        return next_year_balance(employee, leave_type, start, end, application, lock,
                                 half_day, half_day_date)
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
    own_debit = own_debit_in_period(employee, leave_type, application,
        allocation.from_date, allocation.to_date, half_day, half_day_date)
    reserved = pending_in_period(employee, leave_type, allocation.from_date,
                                 allocation.to_date, application)
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


def next_year_balance(employee, leave_type, start, end, application=None, lock=False,
                      half_day=0, half_day_date=None):
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
    if month < 12 or month % 12 or anniversary(joining, month) != next_start or not (getdate(source.from_date) <= start <= end <= next_end and end >= next_start):
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
    current_part = None
    request = frappe._dict(from_date=start, to_date=end, half_day=half_day,
                          half_day_date=half_day_date)
    current_days = days_in_period(employee, leave_type, request, source.from_date, source.to_date)
    if start < next_start:
        current_part = balance_summary(employee, leave_type, start, source.to_date,
            application, half_day=half_day, half_day_date=half_day_date)
    closing_reserved = pending_in_period(employee, leave_type, source.from_date,
                                         source.to_date, application)
    # Recalculate raw closing entitlement: the native calendar cap would reduce
    # a year-end snapshot to one day, which is not the carry-forward balance.
    raw = standard.get_leave_balance_on(employee, leave_type, source.to_date, source.to_date,
        consider_all_leaves_in_the_allocation_period=True, for_consumption=True)
    closing_credit = project_accrual(joining, today, next_start, rules, getdate(source.from_date), next_start)
    own_closing = own_debit_in_period(employee, leave_type, application,
        source.from_date, source.to_date, half_day, half_day_date)
    own = own_debit_in_period(employee, leave_type, application,
        next_start, next_end, half_day, half_day_date)
    carry_limit = flt(leave_doc.maximum_carry_forwarded_leaves)
    carry = min(max(0, flt(raw.get("leave_balance")) + own_closing + closing_credit
                    - closing_reserved - current_days), carry_limit) if leave_doc.is_carry_forward else 0.0
    effective_start = max(start, next_start)
    expiry_days = cint(leave_doc.expire_carry_forwarded_leaves_after_days)
    if expiry_days:
        expiry = getdate(add_days(next_start, expiry_days - 1))
        carry = 0.0 if effective_start > expiry else min(carry, date_diff(expiry, effective_start) + 1)
    credit = project_accrual(joining, next_start, effective_start, rules, next_start, next_end)
    taken = flt(standard.get_leaves_for_period(employee, leave_type, next_start, next_end))
    reserved = pending_in_period(employee, leave_type, next_start, next_end, application)
    available = min(carry + credit + taken + own - reserved, date_diff(next_end, effective_start) + 1)
    current_balance = standard.get_leave_balance_on(employee, leave_type, today, today)
    result = frappe._dict(current_balance=flt(current_balance, 2), projected_accrual=flt(closing_credit + credit, 2),
        pending_reserved=flt(reserved, 2), projected_balance=flt(available, 2),
        projected_carry_forward=flt(carry, 2), carry_forward_limit=carry_limit)
    if current_part is not None:
        result.update(current_period_requested=flt(current_days, 2),
            current_period_balance=current_part.projected_balance,
            next_period_requested=flt(days_in_period(employee, leave_type, request, next_start, next_end), 2),
            next_period_balance=flt(available, 2), next_period_start=str(next_start),
            projected_balance=flt(current_part.projected_balance + available, 2),
            pending_reserved=flt(current_part.pending_reserved + reserved, 2))
    return result


class OrionLeaveApplication(standard.LeaveApplication):
    def create_separate_ledger_entries(self, alloc_on_from_date, alloc_on_to_date, submit, lwp):
        if not uses_projected_balance(self.leave_type):
            return super().create_separate_ledger_entries(alloc_on_from_date, alloc_on_to_date, submit, lwp)
        if (submit and alloc_on_from_date and alloc_on_to_date
                and getdate(add_days(alloc_on_from_date.to_date, 1)) != getdate(alloc_on_to_date.from_date)):
            frappe.throw(_("Leave Application cannot cross non-consecutive leave allocations."))
        # Use the same split for validation and posting. Passing a half-day
        # flag to a one-day segment in the other year would undercharge it.
        boundary = getdate(add_days(alloc_on_from_date.to_date, 1)) if alloc_on_from_date else getdate(alloc_on_to_date.from_date)
        holiday_list = standard.get_holiday_list_for_employee(
            self.employee, raise_exception=not frappe.flags.in_patch) or ""
        request = frappe._dict(from_date=self.from_date, to_date=self.to_date,
            half_day=self.half_day, half_day_date=self.half_day_date, holiday_list=holiday_list)
        for start, end in ((getdate(self.from_date), getdate(add_days(boundary, -1))),
                           (boundary, getdate(self.to_date))):
            days = days_in_period(self.employee, self.leave_type, request, start, end)
            if days:
                standard.create_leave_ledger_entry(self, dict(from_date=start, to_date=end,
                    leaves=-days, is_lwp=lwp, holiday_list=holiday_list), submit)

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
                                  self.to_date, self.name, lock=True,
                                  half_day=self.half_day, half_day_date=self.half_day_date)
        self.custom_current_leave_balance = summary.current_balance
        self.custom_projected_leave_accrual = summary.projected_accrual
        self.custom_pending_leave_reserved = summary.pending_reserved
        self.leave_balance = summary.projected_balance
        self.custom_leave_balance_after = flt(summary.projected_balance - self.total_leave_days, 2)
        if self.is_new() or self.status not in ("Rejected", "Cancelled"):
            if summary.get("current_period_requested", 0) > summary.get("current_period_balance", 0):
                frappe.throw(_("Insufficient projected leave balance before {0}: {1} days available, {2} days requested in the closing leave year.").format(
                    summary.next_period_start, summary.current_period_balance, summary.current_period_requested),
                    exc=standard.InsufficientLeaveBalanceError, title=_("Insufficient Leave Balance"))
            if summary.get("next_period_requested", 0) > summary.get("next_period_balance", 0):
                frappe.throw(_("Insufficient projected leave balance from {0}: {1} days available, {2} days requested in the next leave year. The carry-forward policy limit is {3} days.").format(
                    summary.next_period_start, summary.next_period_balance, summary.next_period_requested, summary.carry_forward_limit),
                    exc=standard.InsufficientLeaveBalanceError, title=_("Insufficient Leave Balance"))
            if flt(self.total_leave_days, 2) > summary.projected_balance:
                frappe.throw(_("Insufficient projected leave balance on {0}: {1} days available, {2} days requested. Pending requests reserve {3} days.").format(
                    self.from_date, summary.projected_balance, self.total_leave_days, summary.pending_reserved),
                    exc=standard.InsufficientLeaveBalanceError, title=_("Insufficient Leave Balance"))


@frappe.whitelist()
def get_projected_leave_balance(employee, leave_type, from_date, to_date, application=None,
                                half_day=0, half_day_date=None):
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
    return balance_summary(employee, leave_type, from_date, to_date, application,
                           half_day=half_day, half_day_date=half_day_date)
