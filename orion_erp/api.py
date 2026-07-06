import frappe
from frappe import _
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from frappe.utils import today

@frappe.whitelist()
def get_customer_focal_person(party_name):
    """
    Given a Customer name, find the first Contact linked to it
    and return the formatted string for custom_customer_focal_person.
    """
    # find the Dynamic Link record
    links = frappe.get_all(
        "Dynamic Link",
        filters={
            "parenttype": "Contact",
            "link_doctype": "Customer",
            "link_name": party_name
        },
        fields=["parent"],
        limit_page_length=1
    )

    if not links:
        return ""

    # load the Contact doc
    contact = frappe.get_doc("Contact", links[0].parent)

    lines = []
    # full name
    full_name = " ".join(filter(None, [
        contact.first_name, contact.middle_name, contact.last_name
    ]))
    if full_name:
        lines.append(full_name)

    # designation (+ company)
    if contact.get("designation"):
        if contact.get("company_name"):
            lines.append(f"{contact.designation} - {contact.company_name}")
        else:
            lines.append(contact.designation)

    # phone / mobile / email
    if contact.get("phone"):
        lines.append(f"Phone: {contact.phone}")
    if contact.get("mobile_no"):
        lines.append(f"Mobile: {contact.mobile_no}")
    if contact.get("email_id"):
        lines.append(f"Email: {contact.email_id}")

    return "\n".join(lines)


# orion_erp/api.py

import frappe
from frappe import _
from frappe.utils import cint

# Reuse HRMS' robust employee fetch logic
from hrms.payroll.doctype.payroll_entry.payroll_entry import (
    get_employee_list,
    get_salary_withholdings,
)



@frappe.whitelist()
def fill_employee_details(filters: dict | None = None, limit: int | None = None, offset: int | None = None):
    """
    Server API for fetching employees for Payroll Entry via orion_erp.
    Mirrors HRMS logic and supports the same filters that the Payroll Entry form builds.

    Args:
        filters: dict with keys like:
          company, start_date, end_date, payroll_frequency, payroll_payable_account,
          currency, department, branch, designation, grade, salary_slip_based_on_timesheet, employees (exclude list)
        limit, offset: optional pagination

    Returns:
        dict: { "employees": [ {employee, employee_name, department, designation, is_salary_withheld}, ... ] }
    """
    # Accept payload from args or HTTP form
    if not filters:
        filters = frappe.form_dict or {}
    filters = frappe._dict(filters)
    
    required = ["company", "currency", "payroll_payable_account", "start_date", "end_date"]
    missing = [f for f in required if not filters.get(f)]
    if missing:
        frappe.throw(
            _("Missing required filters: {0}").format(", ".join(frappe.bold(m) for m in missing)),
            title=_("Validation Error"),
        )

    # Ensure types for pagination
    limit = cint(limit) if limit is not None else None
    offset = cint(offset) if offset is not None else None

    # Pull using HRMS helper (this applies salary structure, dates, payable account, etc.)
    employees = get_employee_list(
        filters=filters,
        searchfield=filters.get("searchfield"),
        search_string=filters.get("txt"),
        fields=["employee", "employee_name", "department", "designation"],
        as_dict=True,
        limit=limit,
        offset=offset,
        ignore_match_conditions=True,  # keep consistent with button UX
    )

    # Tag withheld salaries for the period (same as HRMS flow)
    withheld = set(
        get_salary_withholdings(
            start_date=filters.start_date,
            end_date=filters.end_date,
            pluck="employee",
        )
    )
    for e in employees:
        e["is_salary_withheld"] = 1 if e.get("employee") in withheld else 0

    # Optional: apply a few lightweight post-filters (only if provided)
    # Example extra filters your app may care about (safe to remove if not needed):
    # employment_type, location, project
    post_filters = {
        "employment_type": filters.get("employment_type"),
        "location": filters.get("location"),
        "project": filters.get("project"),
    }
    if any(post_filters.values()):
        emp_ids = [e["employee"] for e in employees]
        if emp_ids:
            # Batch-pull once to avoid N+1
            Employee = frappe.qb.DocType("Employee")
            rows = (
                frappe.qb.from_(Employee)
                .select(Employee.name, Employee.employment_type, Employee.location, Employee.project)
                .where(Employee.name.isin(emp_ids))
            ).run(as_dict=True)
            by_id = {r["name"]: r for r in rows}

            def keep(emp):
                meta = by_id.get(emp["employee"], {})
                for key, want in post_filters.items():
                    if want and (meta.get(key) != want):
                        return False
                return True

            employees = [e for e in employees if keep(e)]

    return {"employees": employees}




@frappe.whitelist()
def get_employee_leave_balance(employee, leave_type, date=None):
    return get_leave_balance_on(
        employee=employee,
        leave_type=leave_type,
        date=date
    )

@frappe.whitelist()
def get_employee_leave_balances():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name"],
        as_dict=True,
    )

    if not employee:
        return []

    allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee.name,
            "docstatus": 1
        },
        fields=["leave_type"]
    )

    data = []

    seen = set()

    for row in allocations:
        if row.leave_type in seen:
            continue

        seen.add(row.leave_type)

        balance = get_leave_balance_on(
            employee.name,
            row.leave_type,
            today()
        )

        data.append({
            "leave_type": row.leave_type,
            "balance": balance
        })

    return data


@frappe.whitelist()
def get_leaves_taken_this_year():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name"],
        as_dict=True,
    )

    if not employee:
        return []

    today_date = frappe.utils.today()

    leave_period = frappe.get_all(
        "Leave Period",
        filters={
            "from_date": ("<=", today_date),
            "to_date": (">=", today_date),
        },
        fields=["from_date", "to_date"],
        limit=1,
    )

    if leave_period:
        from_date = leave_period[0].from_date
        to_date = leave_period[0].to_date
    else:
        from_date = f"{frappe.utils.nowdate()[:4]}-01-01"
        to_date = f"{frappe.utils.nowdate()[:4]}-12-31"

    LeaveApplication = frappe.qb.DocType("Leave Application")

    query = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.leave_type,
            LeaveApplication.total_leave_days,
        )
        .where(LeaveApplication.employee == employee.name)
        .where(LeaveApplication.status == "Approved")
        .where(LeaveApplication.docstatus != 2)
        .where(LeaveApplication.from_date >= from_date)
        .where(LeaveApplication.to_date <= to_date)
    )

    rows = query.run(as_dict=True)

    grouped = {}
    for row in rows:
        lt = row.leave_type
        grouped[lt] = grouped.get(lt, 0) + (float(row.total_leave_days or 0))

    result = [
        {"leave_type": lt, "days_taken": round(days, 1)}
        for lt, days in grouped.items()
    ]

    result.sort(key=lambda x: x["leave_type"])

    return result


@frappe.whitelist()
def get_pending_leave_applications():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name"],
        as_dict=True,
    )

    if not employee:
        return []

    exclude_statuses = ["Approved", "Rejected", "Cancelled"]

    LeaveApplication = frappe.qb.DocType("Leave Application")

    query = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.name,
            LeaveApplication.leave_type,
            LeaveApplication.from_date,
            LeaveApplication.to_date,
            LeaveApplication.total_leave_days,
            LeaveApplication.status,
            LeaveApplication.workflow_state,
            LeaveApplication.custom_approval_status,
        )
        .where(LeaveApplication.employee == employee.name)
        .where(LeaveApplication.docstatus != 2)
        .where(LeaveApplication.status.notin(exclude_statuses))
    )

    rows = query.run(as_dict=True)

    result = []
    for row in rows:
        status = row.custom_approval_status or row.workflow_state or row.status or "Pending"

        result.append({
            "name": row.name,
            "leave_type": row.leave_type,
            "from_date": str(row.from_date or ""),
            "to_date": str(row.to_date or ""),
            "total_days": float(row.total_leave_days or 0),
            "status": status,
        })

    result.sort(key=lambda x: x["from_date"], reverse=True)

    return result


@frappe.whitelist()
def get_approved_upcoming_leaves():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name"],
        as_dict=True,
    )
    if not employee:
        return []

    today_date = frappe.utils.today()

    LeaveApplication = frappe.qb.DocType("Leave Application")

    rows = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.name,
            LeaveApplication.leave_type,
            LeaveApplication.from_date,
            LeaveApplication.to_date,
            LeaveApplication.total_leave_days,
        )
        .where(LeaveApplication.employee == employee.name)
        .where(LeaveApplication.status == "Approved")
        .where(LeaveApplication.docstatus != 2)
        .where(LeaveApplication.from_date >= today_date)
        .orderby(LeaveApplication.from_date)
    ).run(as_dict=True)

    result = []
    for row in rows:
        result.append({
            "name": row.name,
            "leave_type": row.leave_type,
            "from_date": str(row.from_date or ""),
            "to_date": str(row.to_date or ""),
            "total_days": float(row.total_leave_days or 0),
        })

    return result


@frappe.whitelist()
def get_monthly_leave_accrual():
    from orion_erp.orion_erp.scripts.annual_leave_accrual import (
        get_rules_from_leave_type,
        get_rate_for_month,
        get_completed_months,
        LEAVE_TYPE,
    )

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name", "date_of_joining"],
        as_dict=True,
    )
    if not employee:
        return []

    doj = employee.date_of_joining
    if not doj:
        return []

    if isinstance(doj, str):
        from frappe.utils import getdate
        doj = getdate(doj)

    today = frappe.utils.getdate()
    completed_months = get_completed_months(doj, today)
    if completed_months < 1:
        return []

    rules = get_rules_from_leave_type()
    if not rules:
        return []

    monthly_rate = get_rate_for_month(completed_months, rules)
    if monthly_rate <= 0:
        return []

    return [{
        "leave_type": LEAVE_TYPE,
        "earned_days": monthly_rate,
    }]


@frappe.whitelist()
def get_carry_forward_leaves():
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["name", "employee_name"],
        as_dict=True,
    )
    if not employee:
        return []

    today_date = frappe.utils.today()

    LeavePeriod = frappe.qb.DocType("Leave Period")
    current_periods = (
        frappe.qb.from_(LeavePeriod)
        .select(LeavePeriod.name, LeavePeriod.from_date)
        .where(LeavePeriod.from_date <= today_date)
        .where(LeavePeriod.to_date >= today_date)
        .limit(1)
    ).run(as_dict=True)

    if not current_periods:
        return []

    current_from = current_periods[0].from_date
    prev_year_start = frappe.utils.datetime.date(current_from.year - 1, 1, 1)
    prev_year_end = frappe.utils.datetime.date(current_from.year - 1, 12, 31)

    LeaveLedger = frappe.qb.DocType("Leave Ledger Entry")

    rows = (
        frappe.qb.from_(LeaveLedger)
        .select(
            LeaveLedger.leave_type,
            LeaveLedger.transaction_type,
            LeaveLedger.leaves,
        )
        .where(LeaveLedger.employee == employee.name)
        .where(LeaveLedger.transaction_type == "Carry Forward")
        .where(LeaveLedger.from_date >= prev_year_start)
        .where(LeaveLedger.to_date <= prev_year_end)
        .where(LeaveLedger.is_carry_forward == 1)
        .where(LeaveLedger.docstatus == 1)
    ).run(as_dict=True)

    grouped = {}
    for row in rows:
        lt = row.leave_type
        grouped[lt] = grouped.get(lt, 0) + float(row.leaves or 0)

    result = [
        {"leave_type": lt, "carry_forward_days": round(days, 1)}
        for lt, days in grouped.items()
    ]
    result.sort(key=lambda x: x["leave_type"])
    return result