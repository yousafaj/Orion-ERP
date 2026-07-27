import frappe
from frappe import _
from frappe.utils import today, add_years, add_days, flt, getdate, add_months


def validate_allowance_amounts(doc, method=None):
    if doc.custom_site_allowances:
        if not doc.custom_site_allowances_amount or doc.custom_site_allowances_amount <= 0:
            frappe.throw(
                "Site Allowance Amount must be greater than 0 when Site Allowance is checked."
            )

    if doc.custom_offshore_allowances:
        if (
            not doc.custom_offshore_allowances_amount
            or doc.custom_offshore_allowances_amount <= 0
        ):
            frappe.throw(
                "Offshore Allowance Amount must be greater than 0 when Offshore Allowance is checked."
            )


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def user_by_employee(doctype, txt, searchfield, start, page_len, filters):
    users = frappe.db.sql("""
        SELECT
            e.user_id as value,
            CONCAT(e.name, ' - ', e.employee_name) as description
        FROM
            `tabEmployee` e
        WHERE
            e.user_id IS NOT NULL
            AND e.user_id != ''
            AND e.status = 'Active'
            AND (e.name LIKE %(txt)s OR e.employee_name LIKE %(txt)s)
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })
    return users


def create_ticket_allowance():
    settings = frappe.get_single("Orion Settings")
    if not settings.ticket_entitlement_detail:
        return

    employees = frappe.get_all(
        "Employee",
        fields=["name", "designation", "date_of_joining"]
    )
    today_date = getdate(today())

    for emp in employees:
        if not emp.date_of_joining or not emp.designation:
            continue
        _process_employee_ticket_allowance(emp, settings, today_date)
        _update_current_cycle_pro_rata(emp, today_date)


def _process_employee_ticket_allowance(emp, settings, today_date):
    for rule in settings.ticket_entitlement_detail:
        if not rule.designations:
            continue

        designation_list = [d.strip() for d in rule.designations.split(",")]
        if emp.designation not in designation_list:
            continue

        cycle_months = int(flt(rule.eligible_after_years_from_doj) * 12)
        current_start = getdate(emp.date_of_joining)

        while current_start <= today_date:
            _create_ticket_allowance_cycle(emp, rule, current_start, cycle_months)
            current_start = add_months(current_start, cycle_months)


def _create_ticket_allowance_cycle(emp, rule, from_date, cycle_months):
    to_date = add_days(add_months(from_date, cycle_months), -1)

    existing = frappe.db.exists(
        "Ticket Allowance Detail",
        {
            "parent": emp.name,
            "parenttype": "Employee",
            "from_date": ["<=", to_date],
            "to_date": [">=", from_date],
        }
    )
    if existing:
        return

    max_idx = frappe.db.get_value(
        "Ticket Allowance Detail",
        {"parent": emp.name, "parenttype": "Employee"},
        "max(idx)"
    ) or 0

    frappe.get_doc({
        "doctype": "Ticket Allowance Detail",
        "parent": emp.name,
        "parentfield": "custom_ticket_allowance_detail",
        "parenttype": "Employee",
        "from_date": from_date,
        "to_date": to_date,
        "amount": rule.amount,
        "outstanding_amount": rule.amount,
        "paid": 0,
        "pro_rata_amount": 0,
        "idx": max_idx + 1
    }).insert(ignore_permissions=True)


def _update_current_cycle_pro_rata(emp, today_date):
    current_cycle = frappe.db.get_value(
        "Ticket Allowance Detail",
        {
            "parent": emp.name,
            "parenttype": "Employee",
            "from_date": ["<=", today_date],
            "to_date": [">=", today_date]
        },
        ["name", "from_date", "to_date", "amount"],
        as_dict=True
    )
    if not current_cycle:
        return

    from_date = getdate(current_cycle.from_date)
    to_date = getdate(current_cycle.to_date)
    today = getdate(today_date)

    total_months = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)
    if to_date.day >= from_date.day:
        total_months += 1
    if total_months <= 0:
        return

    months_elapsed = (today.year - from_date.year) * 12 + (today.month - from_date.month)
    if today.day < from_date.day:
        months_elapsed -= 1
    months_elapsed = max(0, min(months_elapsed, total_months))
    pro_rata = (flt(current_cycle.amount) / total_months) * months_elapsed

    frappe.db.set_value(
        "Ticket Allowance Detail",
        current_cycle.name,
        "pro_rata_amount",
        flt(pro_rata, 2)
    )


@frappe.whitelist()
def get_manual_paid_lock_date():
    return frappe.db.get_single_value(
        "Orion Settings",
        "manual_paid_check_read_only_date"
    )


def create_salary_structure_assignment(doc, method):
    if not doc.custom_salary_structure or not doc.date_of_joining:
        return

    exists = frappe.db.exists("Salary Structure Assignment", {
        "employee": doc.name,
        "from_date": getdate(doc.date_of_joining),
        "docstatus": ["!=", 2]
    })
    if exists:
        return

    ssa = frappe.new_doc("Salary Structure Assignment")
    ssa.employee = doc.name
    ssa.salary_structure = doc.custom_salary_structure
    ssa.from_date = doc.date_of_joining
    ssa.base = doc.custom_total_salary_as_per_offer_letter or 0
    ssa.company = doc.company
    ssa.insert(ignore_permissions=True)
    ssa.submit()


@frappe.whitelist()
def check_salary_structure_assignment(employee, doj):
    return frappe.db.exists(
        "Salary Structure Assignment",
        {
            "employee": employee,
            "from_date": doj,
            "docstatus": ["!=", 2]
        }
    )


def create_leave_policy_assignment(doc, method):
    leave_policy = _get_leave_policy_for_employee(doc)
    if not leave_policy or not doc.date_of_joining:
        return

    effective_from, effective_to = _get_effective_period(doc.date_of_joining)

    existing = frappe.db.exists("Leave Policy Assignment", {
        "employee": doc.name,
        "effective_from": ["<=", effective_to],
        "effective_to": [">=", effective_from],
        "docstatus": ["in", [0, 1]]
    })
    if existing:
        return

    _validate_no_conflicting_allocations(doc, leave_policy, effective_from, effective_to)
    _create_and_submit_lpa(doc, leave_policy, effective_from, effective_to)


def _get_leave_policy_for_employee(doc):
    gender = doc.get("gender") if isinstance(doc, dict) else getattr(doc, "gender", None)
    if not gender:
        return doc.get("custom_leave_policy") if isinstance(doc, dict) else getattr(doc, "custom_leave_policy", None)

    settings = frappe.get_single("Orion Settings")
    for row in settings.leave_policy_by_gender or []:
        if row.gender == gender:
            return row.leave_policy

    return doc.get("custom_leave_policy") if isinstance(doc, dict) else getattr(doc, "custom_leave_policy", None)


def _get_effective_period(date_of_joining):
    doj = getdate(date_of_joining)
    today_date = getdate()

    completed_months = (today_date.year - doj.year) * 12 + (today_date.month - doj.month)
    if today_date.day < doj.day:
        completed_months -= 1
    completed_months = max(0, completed_months)

    year_start_offset = (completed_months // 12) * 12
    effective_from = add_months(doj, year_start_offset)
    effective_to = add_days(add_months(doj, year_start_offset + 12), -1)
    return effective_from, effective_to


def _validate_no_conflicting_allocations(doc, leave_policy, effective_from, effective_to):
    leave_policy_doc = frappe.get_doc("Leave Policy", leave_policy)
    conflicting = []

    for detail in leave_policy_doc.leave_policy_details:
        if frappe.db.exists("Leave Allocation", {
            "employee": doc.name,
            "leave_type": detail.leave_type,
            "from_date": effective_from,
            "to_date": effective_to,
            "docstatus": 1,
            "expired": 0
        }):
            conflicting.append(detail.leave_type)

    if conflicting:
        frappe.throw(
            _("Leave Allocation(s) already exist for {0} for leave type(s): {1} for period {2} to {3}. Cancel existing allocations before assigning a new leave policy.").format(
                frappe.bold(doc.name),
                frappe.bold(", ".join(conflicting)),
                frappe.bold(str(effective_from)),
                frappe.bold(str(effective_to))
            ),
            title=_("Existing Leave Allocations Found")
        )


def _create_and_submit_lpa(doc, leave_policy, effective_from, effective_to):
    lpa = frappe.new_doc("Leave Policy Assignment")
    lpa.employee = doc.name
    lpa.leave_policy = leave_policy
    lpa.effective_from = effective_from
    lpa.effective_to = effective_to
    lpa.carry_forward = 0
    lpa.insert(ignore_permissions=True)
    lpa.submit()


def auto_renew_leave_policy_assignments():
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "company", "date_of_joining", "gender", "custom_leave_policy"]
    )
    today_date = getdate()

    for emp in employees:
        leave_policy = _get_leave_policy_for_employee(emp)
        if not leave_policy:
            continue

        effective_from, effective_to = _get_effective_period(emp.date_of_joining)
        try:
            _renew_single_employee_lpa(emp, leave_policy, effective_from, effective_to)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Leave Policy Renewal Failed - {emp.name}"
            )


def _renew_single_employee_lpa(emp, leave_policy, effective_from, effective_to):
    existing_lpa = frappe.db.exists("Leave Policy Assignment", {
        "employee": emp.name,
        "effective_from": ["<=", effective_to],
        "effective_to": [">=", effective_from],
        "docstatus": ["in", [0, 1]]
    })
    if existing_lpa:
        return

    leave_policy_doc = frappe.get_doc("Leave Policy", leave_policy)
    for detail in leave_policy_doc.leave_policy_details:
        if frappe.db.exists("Leave Allocation", {
            "employee": emp.name,
            "leave_type": detail.leave_type,
            "from_date": ["<=", effective_to],
            "to_date": [">=", effective_from],
            "docstatus": ["in", [0, 1]],
            "expired": 0
        }):
            return

    lpa = frappe.new_doc("Leave Policy Assignment")
    lpa.employee = emp.name
    lpa.leave_policy = leave_policy
    lpa.effective_from = effective_from
    lpa.effective_to = effective_to
    lpa.carry_forward = 0
    lpa.insert(ignore_permissions=True)
    lpa.submit()


# ──────────────────────────────────────────────────────────────────────
# DOJ CHANGE: validation, cancellation, reallocation, balance adjust
# ──────────────────────────────────────────────────────────────────────

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

    # Always store old DOJ for on_update hooks — even for Administrator
    changes = getattr(frappe.flags, "_employee_doj_changes", None) or {}
    changes[doc.name] = str(getdate(old_doj))
    frappe.flags._employee_doj_changes = changes

    # Skip permission check for Administrator
    if frappe.session.user == "Administrator":
        return

    settings = frappe.get_single("Orion Settings")
    expiry_years = int(flt(getattr(settings, "doj_edit_expiry_years", 0) or 0))

    if expiry_years:
        doj_date = getdate(old_doj)
        expiry_date = add_years(doj_date, expiry_years)
        today_date = getdate()

        if today_date > expiry_date:
            frappe.throw(
                _("DOJ edit period has expired. This employee's DOJ ({0}) is beyond the {1} year edit window ({2}). Only Administrator can change it now.").format(
                    frappe.bold(str(doj_date)),
                    frappe.bold(str(expiry_years)),
                    frappe.bold(str(expiry_date)),
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
    """Get the old DOJ stored during validate hook. Returns None if no change."""
    changes = getattr(frappe.flags, "_employee_doj_changes", None) or {}
    return changes.get(employee)


def _clear_old_doj(employee):
    """Clean up stored old DOJ after processing."""
    changes = getattr(frappe.flags, "_employee_doj_changes", {})
    changes.pop(employee, None)


def cancel_allocations_and_reallocate_on_doj_change(doc, method):
    """When DOJ changes:
    1. Cancel active non-expired allocations and LPAs
    2. Re-create accrual leave type allocations for new DOJ period
    3. Correct ticket allowance dates
    4. create_leave_policy_assignment hook will re-create LPAs with NEW DOJ"""
    if doc.is_new():
        return

    old_doj = _get_old_doj(doc.name)
    if not old_doj:
        return

    try:
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
    """Preserve annual leave balances from active non-expired allocations for this employee."""
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
    """Cancel submitted active leave allocations that are not expired and delete drafts."""
    today = getdate()
    submitted = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "docstatus": 1,
            "expired": 0,
            "to_date": [">=", today],
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
            "to_date": [">=", today],
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
    """Cancel submitted and delete draft leave policy assignments that are not expired."""
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
    """Replay the monthly accrual process for each completed month from new DOJ to today.
    Follows the same logic as annual_leave_accrual.process_employee for each month."""
    from orion_erp.orion_erp.scripts.annual_leave_accrual import (
        get_rules_from_leave_type,
        get_rate_for_month,
        get_completed_months,
        get_year_start,
        get_year_end,
        has_attendance_in_period,
        add_to_existing_allocation,
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
                _accrue_single_month(employee, doj, month_num, rules, leave_type)
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"DOJ Accrual Failed - {employee} - {leave_type} - Month {month_num}"
                )


def _accrue_single_month(employee, doj, month_num, rules, leave_type):
    """Replicate process_employee logic for a single month."""
    from orion_erp.orion_erp.scripts.annual_leave_accrual import (
        get_rate_for_month,
        get_year_start,
        get_year_end,
        has_attendance_in_period,
        add_to_existing_allocation,
    )

    rate = get_rate_for_month(month_num, rules)
    if not rate:
        return

    year_start = get_year_start(doj, month_num)
    year_end = get_year_end(doj, month_num)

    service_start = add_months(doj, month_num - 1)
    service_end = add_days(add_months(doj, month_num), -1)

    description = (
        f"Month {month_num} "
        f"| Allocated: {flt(rate, 2)} days "
        f"({service_start.strftime('%d %B %Y')} - "
        f"{service_end.strftime('%d %B %Y')})"
    )

    already_done = frappe.db.sql(
        """SELECT name FROM `tabLeave Allocation`
        WHERE employee = %s AND leave_type = %s AND docstatus = 1
        AND description LIKE %s""",
        (employee, leave_type, f"%{description}%"),
        pluck=True
    )

    if already_done:
        return

    if not has_attendance_in_period(employee, service_start, service_end):
        return

    if month_num == 6:
        months_with_attendance = 0
        for m in range(1, 7):
            m_start = add_months(doj, m - 1)
            m_end = add_days(add_months(doj, m), -1)
            if has_attendance_in_period(employee, m_start, m_end):
                months_with_attendance += 1

        catch_up = flt(months_with_attendance * 0.5, 2)

        if catch_up > 0:
            description_adj = (
                f"6 Month Adjustment "
                f"| Adjusted: {catch_up} days "
                f"({months_with_attendance} months attended)"
            )

            already_adj = frappe.db.sql(
                """SELECT name FROM `tabLeave Allocation`
                WHERE employee = %s AND leave_type = %s AND docstatus = 1
                AND description LIKE %s""",
                (employee, leave_type, f"%{description_adj}%"),
                pluck=True
            )

            if not already_adj:
                overlap = frappe.db.exists(
                    "Leave Allocation",
                    {
                        "employee": employee,
                        "leave_type": leave_type,
                        "from_date": ["<=", year_end],
                        "to_date": [">=", year_start],
                        "docstatus": 1
                    }
                )

                if overlap:
                    add_to_existing_allocation(overlap, catch_up, description_adj)
                else:
                    allocation = frappe.new_doc("Leave Allocation")
                    allocation.employee = employee
                    allocation.leave_type = leave_type
                    allocation.from_date = year_start
                    allocation.to_date = year_end
                    allocation.new_leaves_allocated = catch_up
                    allocation.description = description_adj
                    allocation.flags.ignore_permissions = True
                    allocation.insert(ignore_permissions=True)
                    allocation.submit()

    overlap = frappe.db.exists(
        "Leave Allocation",
        {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": ["<=", year_end],
            "to_date": [">=", year_start],
            "docstatus": 1
        }
    )

    if overlap:
        add_to_existing_allocation(overlap, flt(rate, 2), description)
        return

    allocation = frappe.new_doc("Leave Allocation")
    allocation.employee = employee
    allocation.leave_type = leave_type
    allocation.from_date = year_start
    allocation.to_date = year_end
    allocation.new_leaves_allocated = flt(rate, 2)
    allocation.description = description
    allocation.flags.ignore_permissions = True
    allocation.insert(ignore_permissions=True)
    allocation.submit()


def _preserve_annual_leave_balances(employee, effective_from, effective_to):
    """Read the balance from the old period's annual leave allocation and store it."""
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
    """Get leave types configured for annual accrual from Orion Settings."""
    settings = frappe.get_single("Orion Settings")
    return [
        row.leave_type
        for row in (getattr(settings, "leave_types_for_accrual", None) or [])
        if row.leave_type
    ]


def _cancel_allocations_for_period(employee, effective_from, effective_to):
    """Cancel submitted and draft leave allocations that overlap with the given period."""
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
    """Cancel submitted and delete draft leave policy assignments that overlap with the given period."""
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


def _correct_ticket_allowance_dates(employee, old_doj, new_doj):
    """When DOJ changes, correct only CURRENT YEAR ticket allowance cycle dates.
    Shifts rows' from_date/to_date so cycles align with the new DOJ.
    Old (non-current-year) rows are left untouched."""
    settings = frappe.get_single("Orion Settings")
    if not settings.ticket_entitlement_detail:
        return

    employee_doc = frappe.get_doc("Employee", employee)
    if not employee_doc.designation:
        return

    cycle_months = None
    for rule in settings.ticket_entitlement_detail:
        if not rule.designations:
            continue
        designation_list = [d.strip() for d in rule.designations.split(",")]
        if employee_doc.designation in designation_list:
            cycle_months = int(flt(rule.eligible_after_years_from_doj) * 12)
            break

    if not cycle_months:
        return

    new_doj_date = getdate(new_doj)
    today_date = getdate()
    current_year = today_date.year
    year_start = f"{current_year}-01-01"
    year_end = f"{current_year}-12-31"

    rows = frappe.get_all(
        "Ticket Allowance Detail",
        filters={
            "parent": employee,
            "parenttype": "Employee",
            "from_date": ["<=", year_end],
            "to_date": [">=", year_start],
        },
        fields=["name", "from_date", "to_date", "amount", "paid", "paid_amount",
                "outstanding_amount", "pro_rata_amount", "idx"],
        order_by="idx asc"
    )

    if not rows:
        return

    old_rows_data = [{
        "from_date": getdate(r.from_date),
        "to_date": getdate(r.to_date),
        "amount": r.amount,
        "paid": r.paid,
        "paid_amount": r.paid_amount,
        "outstanding_amount": r.outstanding_amount,
        "pro_rata_amount": r.pro_rata_amount,
    } for r in rows]

    for row in rows:
        frappe.delete_doc("Ticket Allowance Detail", row.name, ignore_permissions=True)

    current_start = new_doj_date
    idx = 1
    while current_start <= getdate(year_end):
        to_date = add_days(add_months(current_start, cycle_months), -1)

        if to_date >= getdate(year_start) and current_start <= getdate(year_end):
            matched_old = None
            for old_row in old_rows_data:
                old_from = old_row["from_date"]
                old_to = old_row["to_date"]
                if old_from <= to_date and old_to >= current_start:
                    matched_old = old_row
                    break

            new_row_amount = matched_old["amount"] if matched_old else 0
            new_row_paid = matched_old["paid"] if matched_old else 0
            new_row_outstanding = matched_old["outstanding_amount"] if matched_old else 0

            frappe.get_doc({
                "doctype": "Ticket Allowance Detail",
                "parent": employee,
                "parentfield": "custom_ticket_allowance_detail",
                "parenttype": "Employee",
                "from_date": current_start,
                "to_date": to_date,
                "amount": new_row_amount,
                "outstanding_amount": new_row_outstanding,
                "paid": new_row_paid,
                "pro_rata_amount": 0,
                "idx": idx
            }).insert(ignore_permissions=True)

            idx += 1

        current_start = add_months(current_start, cycle_months)

    _update_current_cycle_pro_rata({"name": employee}, today_date)


@frappe.whitelist()
def get_active_leave_allocations_for_employee(employee):
    """Return count of ALL active leave allocations and LPAs for the employee."""
    count = frappe.db.count(
        "Leave Allocation",
        filters={
            "employee": employee,
            "docstatus": 1,
            "expired": 0,
        }
    )

    lpa_count = frappe.db.count(
        "Leave Policy Assignment",
        filters={
            "employee": employee,
            "docstatus": 1,
        }
    )

    return {"allocations": count, "leave_policy_assignments": lpa_count}


@frappe.whitelist()
def is_user_hr_manager():
    """Check if the current user has any of the configured DOJ edit roles."""
    roles = frappe.get_roles(frappe.session.user)
    allowed_roles = _get_doj_edit_roles()
    return 1 if any(r in allowed_roles for r in roles) else 0


@frappe.whitelist()
def can_edit_doj(employee_name):
    """Check if the current user can edit DOJ for this employee.
    Considers both role permissions and the expiry period."""
    if frappe.session.user == "Administrator":
        return {"allowed": True}

    settings = frappe.get_single("Orion Settings")
    expiry_years = int(flt(getattr(settings, "doj_edit_expiry_years", 0) or 0))

    if expiry_years:
        doj = frappe.db.get_value("Employee", employee_name, "date_of_joining")
        if doj:
            expiry_date = add_years(getdate(doj), expiry_years)
            if getdate() > expiry_date:
                return {
                    "allowed": False,
                    "reason": "expired",
                    "doj": str(doj),
                    "expiry_date": str(expiry_date),
                    "expiry_years": expiry_years,
                }

    roles = frappe.get_roles(frappe.session.user)
    allowed_roles = _get_doj_edit_roles()
    if not any(r in allowed_roles for r in roles):
        return {"allowed": False, "reason": "role"}

    return {"allowed": True}


def _get_doj_edit_roles():
    """Get the list of roles allowed to edit DOJ from Orion Settings."""
    settings = frappe.get_single("Orion Settings")
    return [
        row.role
        for row in (getattr(settings, "doj_edit_roles", None) or [])
        if row.role
    ]


def adjust_annual_leave_balance_after_doj_change(doc, method):
    """After LPA recreation, adjust the annual leave allocation balance to match
    what was preserved from the old period's allocation."""
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
    """Adjust a single leave type allocation to have the correct balance."""
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


# ──────────────────────────────────────────────────────────────────────
# Hajj / Umrah
# ──────────────────────────────────────────────────────────────────────

def auto_allocate_hajj_umrah(doc, method):
    if not doc.date_of_joining or doc.custom_religion != "Muslim":
        return

    leave_type = _get_hajj_umrah_leave_type()
    if not leave_type:
        return

    if _has_approved_hajj_leave(doc.name, leave_type):
        return
    if _has_existing_allocation(doc.name, leave_type):
        return

    effective_from, effective_to = _get_effective_period(doc.date_of_joining)
    max_days = frappe.get_value("Leave Type", leave_type, "max_leaves_allowed") or 21

    allocation = frappe.get_doc({
        "doctype": "Leave Allocation",
        "employee": doc.name,
        "leave_type": leave_type,
        "from_date": effective_from,
        "to_date": effective_to,
        "new_leaves_allocated": max_days,
        "carry_forward": 0,
    })
    allocation.insert(ignore_permissions=True)
    allocation.submit()


def _get_hajj_umrah_leave_type():
    settings = frappe.get_single("Orion Settings")
    leave_type_name = getattr(settings, "hajj_umrah_leave_type", None)
    if not leave_type_name:
        return None
    if not frappe.db.exists("Leave Type", {"leave_type_name": leave_type_name}):
        return None
    return frappe.db.get_value("Leave Type", {"leave_type_name": leave_type_name}, "name")


def _has_approved_hajj_leave(employee, leave_type):
    return frappe.db.exists("Leave Application", {
        "employee": employee,
        "leave_type": leave_type,
        "docstatus": 1,
        "status": "Approved"
    })


def _has_existing_allocation(employee, leave_type):
    return frappe.db.exists("Leave Allocation", {
        "employee": employee,
        "leave_type": leave_type,
        "docstatus": 1
    })
