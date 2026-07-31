import frappe
from frappe import _
from frappe.utils import add_years, add_days, flt, getdate, add_months


def validate_doj_readonly(doc, method):
    """Prevent users from changing date_of_joining after it is saved.
    Enforces role-based and time-based restrictions from Orion Settings.
    Stores old DOJ in frappe.flags so on_update hooks can find the old period."""
    if doc.is_new():
        return

    old_doj = frappe.db.get_value("Employee", doc.name, "date_of_joining")
    new_doj = doc.date_of_joining

    if not old_doj or not new_doj:
        return

    if str(getdate(old_doj)) == str(getdate(new_doj)):
        return

    changes = getattr(frappe.flags, "_employee_doj_changes", None) or {}
    changes[doc.name] = str(getdate(old_doj))
    frappe.flags._employee_doj_changes = changes

    if frappe.session.user == "Administrator":
        return

    settings = frappe.get_single("Orion Settings")
    expiry_years = int(flt(getattr(settings, "doj_edit_expiry_years", 0) or 0))

    if expiry_years:
        doj_date = getdate(old_doj)
        expiry_date = add_years(doj_date, expiry_years)
        lock_date = add_days(expiry_date, -1)
        today_date = getdate()

        if today_date >= lock_date:
            frappe.throw(
                _("DOJ can only be edited until {0}. Only Administrator can change it now.").format(
                    frappe.bold(str(lock_date)),
                ),
                title=_("DOJ Edit Period Expired")
            )

    roles = frappe.get_roles(frappe.session.user)
    allowed_roles = _get_doj_edit_roles()
    if not any(r in allowed_roles for r in roles):
        frappe.throw(
            _("Only users with configured DOJ edit roles can change the Date of Joining."),
            title=_("Permission Denied")
        )


def _get_old_doj(employee):
    changes = getattr(frappe.flags, "_employee_doj_changes", None) or {}
    return changes.get(employee)


def _clear_old_doj(employee):
    changes = getattr(frappe.flags, "_employee_doj_changes", {})
    changes.pop(employee, None)


def cancel_allocations_and_reallocate_on_doj_change(doc, method):
    if doc.is_new():
        return

    old_doj = _get_old_doj(doc.name)
    if not old_doj:
        return

    try:
        from .ticket_allowance import _correct_ticket_allowance_dates
        _cancel_all_active_allocations(doc.name)
        _cancel_all_active_lpas(doc.name)
        _recreate_accrual_allocations(doc.name, doc.date_of_joining)
        _correct_ticket_allowance_dates(doc.name, old_doj, doc.date_of_joining)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"DOJ Change Processing Failed - {doc.name}"
        )


def _preserve_annual_leave_balances_current(employee):
    accrual_leave_types = _get_accrual_leave_types()
    today = getdate()
    balances = {}

    for leave_type in accrual_leave_types:
        allocation = frappe.db.get_value(
            "Leave Allocation",
            {
                "employee": employee,
                "leave_type": leave_type,
                "docstatus": 1,
                "expired": 0,
                "to_date": [">=", today],
            },
            ["name", "new_leaves_allocated", "total_leaves_allocated",
             "from_date", "to_date"],
            as_dict=True
        )
        if allocation:
            balances[leave_type] = {
                "name": allocation.name,
                "new_leaves_allocated": flt(allocation.new_leaves_allocated or 0),
                "total_leaves_allocated": flt(allocation.total_leaves_allocated or 0),
                "from_date": allocation.from_date,
                "to_date": allocation.to_date,
            }
    balances_map = getattr(frappe.flags, "_annual_leave_balances", None) or {}
    balances_map[employee] = balances
    frappe.flags._annual_leave_balances = balances_map


def _cancel_all_active_allocations(employee):
    submitted = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "docstatus": 1,
        },
        fields=["name"]
    )

    for alloc in submitted:
        try:
            frappe.get_doc("Leave Allocation", alloc.name).cancel()
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Cancel Leave Allocation Failed - {alloc.name}"
            )

    drafts = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "docstatus": 0,
        },
        fields=["name"]
    )

    for alloc in drafts:
        try:
            frappe.delete_doc("Leave Allocation", alloc.name, ignore_permissions=True)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Delete Draft Leave Allocation Failed - {alloc.name}"
            )


def _cancel_all_active_lpas(employee):
    today = getdate()
    lpas = frappe.get_all(
        "Leave Policy Assignment",
        filters={
            "employee": employee,
            "docstatus": 1,
            "effective_to": [">=", today],
        },
        fields=["name"]
    )
    for lpa in lpas:
        try:
            lpa_doc = frappe.get_doc("Leave Policy Assignment", lpa.name)
            lpa_doc.flags.ignore_links = True
            lpa_doc.cancel()
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Cancel Leave Policy Assignment Failed - {lpa.name}"
            )

    draft_lpas = frappe.get_all(
        "Leave Policy Assignment",
        filters={
            "employee": employee,
            "docstatus": 0,
            "effective_to": [">=", today],
        },
        fields=["name"]
    )

    for lpa in draft_lpas:
        try:
            frappe.delete_doc("Leave Policy Assignment", lpa.name, ignore_permissions=True)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Delete Draft Leave Policy Assignment Failed - {lpa.name}"
            )


def _recreate_accrual_allocations(employee, new_doj):
    from orion_erp.orion_erp.scripts.annual_leave_accrual import (
        process_employee,
        get_rules_from_leave_type,
        get_completed_months,
    )

    accrual_leave_types = _get_accrual_leave_types()
    if not accrual_leave_types:
        return

    doj = getdate(new_doj)
    today = getdate()
    completed_months = get_completed_months(doj, today)

    if completed_months < 1:
        return

    for leave_type in accrual_leave_types:
        rules = get_rules_from_leave_type(leave_type)
        if not rules:
            continue

        for month_num in range(1, completed_months + 1):
            try:
                process_employee(employee, doj, month_num, rules, leave_type)
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"DOJ Accrual Failed - {employee} - {leave_type} - Month {month_num}"
                )


def _preserve_annual_leave_balances(employee, effective_from, effective_to):
    accrual_leave_types = _get_accrual_leave_types()
    balances = {}

    for leave_type in accrual_leave_types:
        allocation = frappe.db.get_value(
            "Leave Allocation",
            {
                "employee": employee,
                "leave_type": leave_type,
                "from_date": effective_from,
                "to_date": effective_to,
                "docstatus": 1,
            },
            ["name", "new_leaves_allocated", "total_leaves_allocated",
             "from_date", "to_date"],
            as_dict=True
        )

        if allocation:
            balances[leave_type] = {
                "name": allocation.name,
                "new_leaves_allocated": flt(allocation.new_leaves_allocated or 0),
                "total_leaves_allocated": flt(allocation.total_leaves_allocated or 0),
                "from_date": allocation.from_date,
                "to_date": allocation.to_date,
            }

    balances_map = getattr(frappe.flags, "_annual_leave_balances", None) or {}
    balances_map[employee] = balances
    frappe.flags._annual_leave_balances = balances_map


def _get_accrual_leave_types():
    settings = frappe.get_single("Orion Settings")
    return [
        row.leave_type
        for row in (getattr(settings, "leave_types_for_accrual", None) or [])
        if row.leave_type
    ]


def _cancel_allocations_for_period(employee, effective_from, effective_to):
    submitted = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "docstatus": 1,
            "expired": 0,
            "from_date": ["<=", effective_to],
            "to_date": [">=", effective_from],
        },
        fields=["name"]
    )

    for alloc in submitted:
        try:
            frappe.get_doc("Leave Allocation", alloc.name).cancel()
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Cancel Leave Allocation Failed - {alloc.name}"
            )

    drafts = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "docstatus": 0,
            "from_date": ["<=", effective_to],
            "to_date": [">=", effective_from],
        },
        fields=["name"]
    )

    for alloc in drafts:
        try:
            frappe.delete_doc("Leave Allocation", alloc.name, ignore_permissions=True)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Delete Draft Leave Allocation Failed - {alloc.name}"
            )


def _cancel_lpa_for_period(employee, effective_from, effective_to):
    lpas = frappe.get_all(
        "Leave Policy Assignment",
        filters={
            "employee": employee,
            "docstatus": 1,
            "effective_from": ["<=", effective_to],
            "effective_to": [">=", effective_from],
        },
        fields=["name"]
    )

    for lpa in lpas:
        try:
            frappe.get_doc("Leave Policy Assignment", lpa.name).cancel()
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Cancel Leave Policy Assignment Failed - {lpa.name}"
            )

    draft_lpas = frappe.get_all(
        "Leave Policy Assignment",
        filters={
            "employee": employee,
            "docstatus": 0,
            "effective_from": ["<=", effective_to],
            "effective_to": [">=", effective_from],
        },
        fields=["name"]
    )

    for lpa in draft_lpas:
        try:
            frappe.delete_doc("Leave Policy Assignment", lpa.name, ignore_permissions=True)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Delete Draft Leave Policy Assignment Failed - {lpa.name}"
            )


@frappe.whitelist()
def get_active_leave_allocations_for_employee(employee):
    today = getdate()
    count = frappe.db.count(
        "Leave Allocation",
        filters={
            "employee": employee,
            "docstatus": 1,
        }
    )

    lpa_count = frappe.db.count(
        "Leave Policy Assignment",
        filters={
            "employee": employee,
            "docstatus": 1,
            "effective_to": [">=", today],
        }
    )

    return {"allocations": count, "leave_policy_assignments": lpa_count}


@frappe.whitelist()
def is_user_hr_manager():
    roles = frappe.get_roles(frappe.session.user)
    allowed_roles = _get_doj_edit_roles()
    return 1 if any(r in allowed_roles for r in roles) else 0


@frappe.whitelist()
def can_edit_doj(employee_name):
    if frappe.session.user == "Administrator":
        return {"allowed": True}

    settings = frappe.get_single("Orion Settings")
    expiry_years = int(flt(getattr(settings, "doj_edit_expiry_years", 0) or 0))

    if expiry_years:
        doj = frappe.db.get_value("Employee", employee_name, "date_of_joining")
        if doj:
            expiry_date = add_years(getdate(doj), expiry_years)
            lock_date = add_days(expiry_date, -1)
            if getdate() >= lock_date:
                return {
                    "allowed": False,
                    "reason": "expired",
                    "doj": str(doj),
                    "lock_date": str(lock_date),
                    "expiry_years": expiry_years,
                }

    roles = frappe.get_roles(frappe.session.user)
    allowed_roles = _get_doj_edit_roles()
    if not any(r in allowed_roles for r in roles):
        return {"allowed": False, "reason": "role"}

    return {"allowed": True}


def _get_doj_edit_roles():
    settings = frappe.get_single("Orion Settings")
    return [
        row.role
        for row in (getattr(settings, "doj_edit_roles", None) or [])
        if row.role
    ]


def adjust_annual_leave_balance_after_doj_change(doc, method):
    if doc.is_new():
        return

    old_doj = _get_old_doj(doc.name)
    if not old_doj:
        return

    try:
        preserved = getattr(frappe.flags, "_annual_leave_balances", {}).get(doc.name, {})
        if not preserved:
            return

        for leave_type, old_data in preserved.items():
            _adjust_single_leave_type_balance(
                doc.name, leave_type, old_data
            )

        balances_map = getattr(frappe.flags, "_annual_leave_balances", None)
        if balances_map:
            balances_map.pop(doc.name, None)
        _clear_old_doj(doc.name)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"DOJ Balance Adjustment Failed - {doc.name}"
        )


def _adjust_single_leave_type_balance(employee, leave_type, old_data):
    new_allocation = frappe.db.get_value(
        "Leave Allocation",
        {
            "employee": employee,
            "leave_type": leave_type,
            "docstatus": 1,
            "expired": 0,
        },
        ["name", "new_leaves_allocated", "total_leaves_allocated",
         "from_date", "to_date"],
        as_dict=True
    )

    if not new_allocation:
        return

    correct_balance = old_data["new_leaves_allocated"]

    if flt(new_allocation.new_leaves_allocated) == correct_balance:
        return

    frappe.db.set_value(
        "Leave Allocation",
        new_allocation.name,
        {
            "new_leaves_allocated": correct_balance,
            "total_leaves_allocated": correct_balance,
        }
    )

    adjustment = correct_balance - flt(new_allocation.new_leaves_allocated)
    if adjustment != 0:
        employee_doc = frappe.get_doc("Employee", employee)
        ledger = frappe.get_doc({
            "doctype": "Leave Ledger Entry",
            "employee": employee,
            "leave_type": leave_type,
            "transaction_type": "Leave Allocation",
            "transaction_name": new_allocation.name,
            "leaves": adjustment,
            "from_date": new_allocation.from_date,
            "to_date": new_allocation.to_date,
            "is_carry_forward": 0,
            "is_expired": 0,
            "is_lwp": 0,
            "company": employee_doc.company,
        })
        ledger.flags.ignore_permissions = True
        ledger.submit()
