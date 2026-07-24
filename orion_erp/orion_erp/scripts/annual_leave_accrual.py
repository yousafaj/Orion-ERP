import frappe
from frappe.utils import getdate, add_months, add_days, flt
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import (
    expire_allocation,
    get_remaining_leaves,
)
from orion_erp.orion_erp.scripts.excess_leave_notification import (
    notify_excess_leaves,
)


def get_configured_leave_types():
    settings = frappe.get_single("Orion Settings")
    return [
        row.leave_type
        for row in (getattr(settings, "leave_types_for_accrual", None) or [])
        if row.leave_type
    ]


def add_to_existing_allocation(allocation_name, additional_leaves, description=None):
    current = frappe.db.get_value(
        "Leave Allocation",
        allocation_name,
        ["new_leaves_allocated", "total_leaves_allocated", "employee",
         "leave_type", "from_date", "to_date", "company", "description"],
        as_dict=True
    )

    new_new = flt(current.new_leaves_allocated or 0) + additional_leaves
    new_total = frappe.db.get_value(
        "Leave Allocation",
        allocation_name,
        "total_leaves_allocated"
    )

    update_fields = {
        "new_leaves_allocated": new_new,
        "total_leaves_allocated": flt(new_total or 0) + additional_leaves,
    }

    if description:
        existing_desc = current.description or ""
        if description not in existing_desc:
            update_fields["description"] = f"{existing_desc}\n{description}".strip()

    frappe.db.set_value(
        "Leave Allocation",
        allocation_name,
        update_fields
    )

    ledger = frappe.get_doc({
        "doctype": "Leave Ledger Entry",
        "employee": current.employee,
        "leave_type": current.leave_type,
        "transaction_type": "Leave Allocation",
        "transaction_name": allocation_name,
        "leaves": additional_leaves,
        "from_date": current.from_date,
        "to_date": current.to_date,
        "is_carry_forward": 0,
        "is_expired": 0,
        "is_lwp": 0,
        "company": current.company,
    })
    ledger.flags.ignore_permissions = True
    ledger.submit()


def execute_monthly_accrual():
    leave_types = get_configured_leave_types()

    if not leave_types:
        return

    today = getdate()

    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "date_of_joining": ["<=", today]
        },
        fields=["name", "date_of_joining"]
    )

    for leave_type in leave_types:
        rules = get_rules_from_leave_type(leave_type)

        if not rules:
            continue

        for emp in employees:
            try:
                doj = getdate(emp.date_of_joining)

                completed_months = get_completed_months(doj, today)

                if completed_months < 1:
                    continue

                anniversary_date = add_months(doj, completed_months)

                if anniversary_date != today:
                    continue

                process_employee(
                    emp.name,
                    doj,
                    completed_months,
                    rules,
                    leave_type
                )

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Monthly Accrual Failed - {emp.name} - {leave_type}"
                )


def process_employee(employee, doj, month_num, rules, leave_type):
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


def get_rules_from_leave_type(leave_type):
    leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

    rules = sorted(
        leave_type_doc.custom_annual_leave_accrual_rules or [],
        key=lambda x: x.from_months
    )

    return [
        {
            "from_months": r.from_months,
            "to_months": r.to_months,
            "days_per_month": flt(r.days_per_month)
        }
        for r in rules
    ]


def get_rate_for_month(month_num, rules):
    for rule in rules:

        if rule["to_months"] == 0:
            if month_num >= rule["from_months"]:
                return rule["days_per_month"]

        elif rule["from_months"] <= month_num <= rule["to_months"]:
            return rule["days_per_month"]

    return 0


def get_completed_months(from_date, to_date):
    months = (
        (to_date.year - from_date.year) * 12
        + (to_date.month - from_date.month)
    )

    if to_date.day < from_date.day:
        months -= 1

    return max(months, 0)


def get_year_start(doj, month_num):
    anniversary_index = ((month_num - 1) // 12) * 12
    return add_months(doj, anniversary_index)


def get_year_end(doj, month_num):
    anniversary_index = ((month_num - 1) // 12) * 12
    return add_days(
        add_months(doj, anniversary_index + 12),
        -1
    )


def has_attendance_in_period(employee, from_date, to_date):
    return frappe.db.exists(
        "Attendance",
        {
            "employee": employee,
            "attendance_date": ["between", [from_date, to_date]],
            "status": ["in", ["Present", "Half Day"]],
            "docstatus": 1
        }
    )


def execute_carry_forward():
    leave_types = get_configured_leave_types()

    if not leave_types:
        return

    today = getdate()

    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "date_of_joining": ["<=", today]
        },
        fields=["name", "employee_name", "date_of_joining"]
    )

    for leave_type in leave_types:
        leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

        max_carry = flt(
            leave_type_doc.maximum_carry_forwarded_leaves or 0
        )

        if not max_carry:
            continue

        for emp in employees:
            doj = getdate(emp.date_of_joining)

            completed_months = get_completed_months(
                doj,
                today
            )

            if (
                completed_months < 12
                or completed_months % 12 != 0
            ):
                continue

            anniversary_date = add_months(
                doj,
                completed_months
            )

            if anniversary_date != today:
                continue

            leave_year_end = add_days(
                add_months(doj, completed_months),
                -1
            )

            try:
                balance = flt(
                    get_leave_balance_on(
                        emp.name,
                        leave_type,
                        leave_year_end
                    )
                )

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Carry Forward Balance Failed - {emp.name} - {leave_type}"
                )
                continue

            carry_forward = min(
                balance,
                max_carry
            )

            cf_from = add_months(doj, completed_months)

            expire_previous_allocation(emp.name, cf_from, leave_type)

            if carry_forward <= 0:
                continue

            description = (
                f"Carry Forward Year {completed_months // 12} "
                f"| Carry Forward: {carry_forward} days "
                f"(Balance: {balance}, Max: {max_carry})"
            )

            allocation_name, excess = create_carry_forward(
                emp.name,
                doj,
                completed_months,
                max_carry,
                leave_type
            )

            if allocation_name and excess > 0:
                # print(f"Notifying excess leave for {emp.name}: {excess} days excess, allocation={allocation_name}")
                notify_excess_leaves(
                    emp.name,
                    allocation_name,
                    excess,
                    max_carry
                )

def test1():
    rules = get_rules_from_leave_type("ANNUAL LEAVE")

    name, excess = create_carry_forward(
        employee="HR-EMP-00379",
        doj=getdate("2026-05-05"),
        completed_months=12,
        max_carry=10,
        leave_type="ANNUAL LEAVE"
    )
    if name:
        # print(f"Created CF allocation: {name}, excess={excess}")
        if excess > 0:
            # print(f"Excess found: {excess} days. Sending notification...")
            notify_excess_leaves(
                employee="HR-EMP-00379",
                allocation_name=name,
                excess_days=excess,
                max_carry=15
            )

def create_carry_forward(
    employee,
    doj,
    completed_months,
    max_carry,
    leave_type
):
    leave_year_end = add_days(
        add_months(doj, completed_months),
        -1
    )

    balance = flt(
        get_leave_balance_on(
            employee,
            leave_type,
            leave_year_end
        )
    )

    carry_forward = min(
        balance,
        max_carry
    )

    excess = max(0, balance - max_carry)

    if carry_forward <= 0:
        return None, 0

    description = (
        f"Carry Forward Year {completed_months // 12} "
        f"| Carry Forward: {carry_forward} days "
        f"(Balance: {balance}, Max: {max_carry})"
    )

    existing = frappe.db.sql(
        """SELECT name, docstatus, custom_excess_leave_days
        FROM `tabLeave Allocation`
        WHERE employee = %s AND leave_type = %s
        AND description LIKE %s
        ORDER BY docstatus ASC, creation DESC""",
        (employee, leave_type, f"%{description}%"),
        as_dict=True
    )

    # If a draft amendment already exists, return it
    for row in existing:
        if row.docstatus == 0:
            needs_save = False
            if flt(row.custom_excess_leave_days) != excess:
                frappe.db.set_value("Leave Allocation", row.name, "custom_excess_leave_days", excess)
            current_nla = frappe.db.get_value("Leave Allocation", row.name, "new_leaves_allocated")
            current_status = frappe.db.get_value("Leave Allocation", row.name, "custom_excess_leave_status")
            current_cf = flt(frappe.db.get_value("Leave Allocation", row.name, "custom_carry_forward_days"))
            current_lapsed = flt(frappe.db.get_value("Leave Allocation", row.name, "custom_lapsed_leave_days"))

            if current_status == "Extend" and flt(current_cf + current_lapsed) != excess:
                frappe.db.set_value("Leave Allocation", row.name, "custom_excess_leave_status", "Pending")
                frappe.db.set_value("Leave Allocation", row.name, "custom_carry_forward_days", 0)
                frappe.db.set_value("Leave Allocation", row.name, "custom_lapsed_leave_days", 0)
                frappe.db.set_value("Leave Allocation", row.name, "new_leaves_allocated", carry_forward)
                frappe.db.set_value("Leave Allocation", row.name, "total_leaves_allocated", carry_forward)
            elif flt(current_nla) != carry_forward and current_status == "Pending":
                frappe.db.set_value("Leave Allocation", row.name, "new_leaves_allocated", carry_forward)
                frappe.db.set_value("Leave Allocation", row.name, "total_leaves_allocated", carry_forward)
            return row.name, excess

    # If a submitted allocation exists, update it and create an amended draft if excess > 0
    for row in existing:
        if row.docstatus == 1:
            if flt(row.custom_excess_leave_days) != excess:
                frappe.db.set_value("Leave Allocation", row.name, "custom_excess_leave_days", excess)
                frappe.db.set_value("Leave Allocation", row.name, "custom_excess_leave_status", "Pending")
            if excess > 0:
                from frappe.model import copy_doc
                amend_allocation = copy_doc(frappe.get_doc("Leave Allocation", row.name))
                amend_allocation.docstatus = 0
                amend_allocation.new_leaves_allocated = carry_forward
                amend_allocation.total_leaves_allocated = carry_forward
                amend_allocation.custom_excess_leave_days = excess
                amend_allocation.custom_excess_leave_status = "Pending"
                amend_allocation.flags.ignore_permissions = True
                amend_allocation.insert(ignore_permissions=True)
                return amend_allocation.name, excess
            return row.name, excess

    cf_from = add_months(doj, completed_months)
    cf_to = add_days(add_months(doj, completed_months + 12), -1)

    overlap = frappe.db.exists(
        "Leave Allocation",
        {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": ["<=", cf_to],
            "to_date": [">=", cf_from],
            "docstatus": 1
        }
    )

    if overlap:
        add_to_existing_allocation(overlap, carry_forward, description)
        if excess > 0:
            frappe.db.set_value("Leave Allocation", overlap, "custom_excess_leave_days", excess)
            frappe.db.set_value("Leave Allocation", overlap, "custom_excess_leave_status", "Pending")
        return overlap, excess

    allocation = frappe.new_doc(
        "Leave Allocation"
    )

    allocation.employee = employee
    allocation.leave_type = leave_type
    allocation.from_date = cf_from
    allocation.to_date = cf_to
    allocation.new_leaves_allocated = carry_forward
    allocation.description = description
    allocation.custom_excess_leave_days = excess
    allocation.custom_excess_leave_status = "Pending"

    allocation.flags.ignore_permissions = True

    allocation.insert(
        ignore_permissions=True
    )

    if excess > 0:
        expire_previous_allocation(employee, cf_from, leave_type)
    else:
        allocation.submit()
        expire_previous_allocation(employee, cf_from, leave_type)

    return allocation.name, excess


def expire_previous_allocation(employee, new_year_start, leave_type):
    prev_allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "to_date": ["<", new_year_start],
            "docstatus": 1,
            "expired": 0,
        },
        fields=["name", "to_date"],
        order_by="to_date desc"
    )

    for alloc in prev_allocations:
        doc = frappe.get_doc("Leave Allocation", alloc.name)
        remaining = get_remaining_leaves(doc)

        if remaining and remaining > 0:
            expire_allocation(doc)
