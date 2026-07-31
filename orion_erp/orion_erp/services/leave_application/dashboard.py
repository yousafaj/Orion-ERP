import frappe
from frappe.query_builder.functions import Sum
from frappe.utils import getdate, today


@frappe.whitelist()
@frappe.read_only()
def get_org_leave_summary():
    Employee = frappe.qb.DocType("Employee")
    LeaveAllocation = frappe.qb.DocType("Leave Allocation")
    LeaveLedger = frappe.qb.DocType("Leave Ledger Entry")

    today_date = frappe.utils.today()

    total_employees = frappe.db.count("Employee", filters={"status": "Active"})

    allocations = (
        frappe.qb.from_(LeaveAllocation)
        .select(
            LeaveAllocation.employee,
            LeaveAllocation.leave_type,
            LeaveAllocation.new_leaves_allocated,
        )
        .where(LeaveAllocation.docstatus == 1)
        .where(LeaveAllocation.from_date <= today_date)
        .where(LeaveAllocation.to_date >= today_date)
        .orderby(LeaveAllocation.employee)
        .limit(2000)
    ).run(as_dict=True)

    emp_names = list(set(r["employee"] for r in allocations))
    emp_map = {}
    if emp_names:
        emp_data = (
            frappe.qb.from_(Employee)
            .select(Employee.name, Employee.employee_name, Employee.department)
            .where(Employee.name.isin(emp_names))
        ).run(as_dict=True)
        emp_map = {e["name"]: e for e in emp_data}

    emp_with_alloc_count = len(set(r["employee"] for r in allocations))

    ledger_balances = {}
    if emp_names:
        balance_data = (
            frappe.qb.from_(LeaveLedger)
            .select(
                LeaveLedger.employee,
                LeaveLedger.leave_type,
                Sum(LeaveLedger.leaves).as_("balance"),
            )
            .where(LeaveLedger.docstatus == 1)
            .where(LeaveLedger.is_carry_forward == 0)
            .where(LeaveLedger.is_expired == 0)
            .where(LeaveLedger.employee.isin(emp_names))
            .groupby(LeaveLedger.employee, LeaveLedger.leave_type)
        ).run(as_dict=True)
        for b in balance_data:
            key = (b["employee"], b["leave_type"])
            ledger_balances[key] = float(b["balance"] or 0)

    detail = []
    for r in allocations:
        e = emp_map.get(r["employee"], {})
        key = (r["employee"], r["leave_type"])
        bal = ledger_balances.get(key, 0)
        detail.append({
            "employee": r["employee"],
            "employee_name": e.get("employee_name", ""),
            "department": e.get("department", ""),
            "leave_type": r["leave_type"],
            "available_balance": bal,
        })

    total_balance = sum(d["available_balance"] for d in detail)
    avg_balance = round(total_balance / emp_with_alloc_count, 1) if emp_with_alloc_count else 0

    return {
        "kpi": {
            "total_employees": total_employees,
            "employees_with_allocation": emp_with_alloc_count,
            "total_balance": round(total_balance, 1),
            "avg_balance": avg_balance,
        },
        "rows": detail,
    }


@frappe.whitelist()
@frappe.read_only()
def get_employees_on_leave_today():
    LeaveApplication = frappe.qb.DocType("Leave Application")
    today_date = frappe.utils.today()

    rows = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.name,
            LeaveApplication.employee,
            LeaveApplication.employee_name,
            LeaveApplication.department,
            LeaveApplication.leave_type,
            LeaveApplication.from_date,
            LeaveApplication.to_date,
            LeaveApplication.leave_approver,
            LeaveApplication.status,
        )
        .where(LeaveApplication.docstatus == 1)
        .where(LeaveApplication.status != "Cancelled")
        .where(LeaveApplication.from_date <= today_date)
        .where(LeaveApplication.to_date >= today_date)
        .orderby(LeaveApplication.employee_name)
        .limit(2000)
    ).run(as_dict=True)

    departments = set()
    leave_types = set()
    for r in rows:
        if r.get("department"):
            departments.add(r["department"])
        if r.get("leave_type"):
            leave_types.add(r["leave_type"])

    return {
        "kpi": {
            "employees_on_leave": len(rows),
            "departments_impacted": len(departments),
            "leave_types_count": len(leave_types),
            "today_date": today_date,
        },
        "rows": rows,
    }


@frappe.whitelist()
@frappe.read_only()
def get_pending_approvals_48h():
    LeaveApplication = frappe.qb.DocType("Leave Application")

    from frappe.utils import now_datetime

    now = now_datetime()
    rows = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.name,
            LeaveApplication.employee,
            LeaveApplication.employee_name,
            LeaveApplication.department,
            LeaveApplication.leave_type,
            LeaveApplication.posting_date,
            LeaveApplication.creation,
            LeaveApplication.leave_approver,
            LeaveApplication.status,
            LeaveApplication.custom_approval_status,
            LeaveApplication.workflow_state,
        )
        .where(LeaveApplication.docstatus == 0)
        .where(
            (LeaveApplication.status == "Open")
            | (LeaveApplication.status.like("Pending%"))
        )
        .orderby(LeaveApplication.creation)
        .limit(2000)
    ).run(as_dict=True)

    pending_count = len(rows)
    older_48h = 0
    total_wait_hours = 0
    max_wait_hours = 0

    results = []
    for r in rows:
        created = frappe.utils.get_datetime(r["creation"])
        wait_hours = round((now - created).total_seconds() / 3600, 1)
        total_wait_hours += wait_hours
        if wait_hours > max_wait_hours:
            max_wait_hours = wait_hours
        if wait_hours > 48:
            older_48h += 1

        approver = r.get("leave_approver") or ""
        status = r.get("custom_approval_status") or r.get("workflow_state") or r.get("status") or "Open"

        results.append({
            "name": r["name"],
            "employee": r["employee"],
            "employee_name": r.get("employee_name", ""),
            "department": r.get("department", ""),
            "leave_type": r.get("leave_type", ""),
            "posting_date": str(r.get("posting_date") or ""),
            "waiting_hours": wait_hours,
            "approver": approver,
            "status": status,
        })

    avg_wait = round(total_wait_hours / pending_count, 1) if pending_count else 0

    return {
        "kpi": {
            "pending_requests": pending_count,
            "older_than_48h": older_48h,
            "avg_waiting_hours": avg_wait,
            "max_waiting_hours": round(max_wait_hours, 1),
        },
        "rows": results,
    }


@frappe.whitelist()
@frappe.read_only()
def get_missing_medical_certificates():
    LeaveApplication = frappe.qb.DocType("Leave Application")

    rows = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.name,
            LeaveApplication.employee,
            LeaveApplication.employee_name,
            LeaveApplication.leave_type,
            LeaveApplication.from_date,
            LeaveApplication.to_date,
            LeaveApplication.total_leave_days,
            LeaveApplication.status,
        )
        .where(LeaveApplication.docstatus == 1)
        .where(LeaveApplication.leave_type.like("%Sick%") | LeaveApplication.leave_type.like("%Medical%"))
        .where(LeaveApplication.status != "Cancelled")
        .orderby(LeaveApplication.creation, order=frappe.qb.desc)
        .limit(2000)
    ).run(as_dict=True)

    total_sick = len(rows)
    missing = []
    uploaded = 0

    for r in rows:
        has_cert = bool(
            frappe.db.get_value(
                "File",
                {
                    "attached_to_doctype": "Leave Application",
                    "attached_to_name": r["name"],
                },
                "name",
            )
        )
        if has_cert:
            uploaded += 1
        else:
            missing.append(r)

    compliance_pct = round((uploaded / total_sick * 100), 1) if total_sick else 0

    detail = []
    for r in missing:
        detail.append({
            "name": r["name"],
            "employee": r["employee"],
            "employee_name": r.get("employee_name", ""),
            "leave_type": r.get("leave_type", ""),
            "total_days": float(r.get("total_leave_days") or 0),
            "medical_certificate": "Missing",
            "status": r.get("status", ""),
        })

    return {
        "kpi": {
            "total_sick_leaves": total_sick,
            "missing_certificates": len(missing),
            "uploaded_certificates": uploaded,
            "compliance_pct": compliance_pct,
        },
        "rows": detail,
    }


@frappe.whitelist()
@frappe.read_only()
def get_leave_encashment_requests():
    Encashment = frappe.qb.DocType("Leave Encashment")

    rows = (
        frappe.qb.from_(Encashment)
        .select(
            Encashment.name,
            Encashment.employee,
            Encashment.employee_name,
            Encashment.department,
            Encashment.leave_type,
            Encashment.encashment_days,
            Encashment.encashment_amount,
            Encashment.status,
            Encashment.creation,
        )
        .where(Encashment.docstatus == 0)
        .where(Encashment.status == "Draft")
        .orderby(Encashment.creation)
        .limit(2000)
    ).run(as_dict=True)

    pending = len(rows)
    total_days = 0
    total_amount = 0.0
    oldest = None

    detail = []
    for r in rows:
        days = float(r.get("encashment_days") or 0)
        amount = float(r.get("encashment_amount") or 0)
        total_days += days
        total_amount += amount
        if oldest is None or r["creation"] < oldest:
            oldest = r["creation"]

        detail.append({
            "name": r["name"],
            "employee": r["employee"],
            "employee_name": r.get("employee_name", ""),
            "department": r.get("department", ""),
            "leave_type": r.get("leave_type", ""),
            "encashment_days": days,
            "encashment_amount": amount,
            "status": r.get("status", "Draft"),
        })

    return {
        "kpi": {
            "pending_requests": pending,
            "total_encashment_days": round(total_days, 1),
            "estimated_amount": round(total_amount, 2),
            "oldest_request": str(oldest.date()) if oldest else "N/A",
        },
        "rows": detail,
    }


@frappe.whitelist()
@frappe.read_only()
def get_pending_leave_status():
    LeaveApplication = frappe.qb.DocType("Leave Application")

    from frappe.utils import now_datetime
    now = now_datetime()

    rows = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.name,
            LeaveApplication.employee,
            LeaveApplication.employee_name,
            LeaveApplication.department,
            LeaveApplication.leave_type,
            LeaveApplication.posting_date,
            LeaveApplication.creation,
            LeaveApplication.leave_approver,
            LeaveApplication.custom_leave_approver_1,
            LeaveApplication.custom_leave_approver_2,
            LeaveApplication.custom_leave_approver_4,
            LeaveApplication.custom_leave_approver_5,
            LeaveApplication.status,
            LeaveApplication.custom_approval_status,
            LeaveApplication.workflow_state,
        )
        .where(LeaveApplication.docstatus == 0)
        .where(
            (LeaveApplication.status == "Open")
            | (LeaveApplication.status.like("Pending%"))
        )
        .orderby(LeaveApplication.creation, order=frappe.qb.desc)
        .limit(2000)
    ).run(as_dict=True)

    total_pending = len(rows)
    manager_pending = 0
    hr_pending = 0
    final_pending = 0

    detail = []
    for r in rows:
        created = frappe.utils.get_datetime(r["creation"])
        age_days = round((now - created).total_seconds() / 86400, 1)

        wf = r.get("custom_approval_status") or r.get("workflow_state") or r.get("status") or "Open"

        current_approver = r.get("leave_approver") or ""
        wf_lower = wf.lower()

        if "approver 4" in wf_lower or "approver 5" in wf_lower:
            final_pending += 1
        elif "approver 2" in wf_lower or "approver 3" in wf_lower:
            hr_pending += 1
        elif "approver 1" in wf_lower or "open" in wf_lower:
            manager_pending += 1
        else:
            manager_pending += 1

        detail.append({
            "name": r["name"],
            "employee": r["employee"],
            "employee_name": r.get("employee_name", ""),
            "leave_type": r.get("leave_type", ""),
            "posting_date": str(r.get("posting_date") or ""),
            "current_approver": current_approver,
            "workflow_state": wf,
            "age_days": age_days,
            "status": r.get("status", "Open"),
        })

    return {
        "kpi": {
            "total_pending": total_pending,
            "manager_pending": manager_pending,
            "hr_pending": hr_pending,
            "final_pending": final_pending,
        },
        "rows": detail,
    }


@frappe.whitelist()
@frappe.read_only()
def get_monthly_accrual_status():
    LeaveAllocation = frappe.qb.DocType("Leave Allocation")
    Employee = frappe.qb.DocType("Employee")
    today_date = frappe.utils.today()
    today = frappe.utils.datetime.date.today()
    current_month_start = today.replace(day=1)
    next_month = current_month_start.replace(month=current_month_start.month % 12 + 1, day=1) if current_month_start.month < 12 else current_month_start.replace(year=current_month_start.year + 1, month=1, day=1)
    current_month_end = next_month - frappe.utils.datetime.timedelta(days=1)
    month_end_str = frappe.utils.formatdate(current_month_end, "yyyy-mm-dd")
    month_start_str = frappe.utils.formatdate(current_month_start, "yyyy-mm-dd")

    total_active = frappe.db.count("Employee", filters={"status": "Active"})

    allocations = (
        frappe.qb.from_(LeaveAllocation)
        .select(
            LeaveAllocation.name,
            LeaveAllocation.employee,
            LeaveAllocation.leave_type,
            LeaveAllocation.new_leaves_allocated,
            LeaveAllocation.from_date,
            LeaveAllocation.to_date,
            LeaveAllocation.creation,
        )
        .where(LeaveAllocation.docstatus == 1)
        .where(LeaveAllocation.leave_type.like("Annual Leave"))
        .where(LeaveAllocation.from_date >= month_start_str)
        .where(LeaveAllocation.from_date <= month_end_str)
        .orderby(LeaveAllocation.creation, order=frappe.qb.desc)
        .limit(2000)
    ).run(as_dict=True)

    allocated_employees = set(r["employee"] for r in allocations)
    allocated_count = len(allocated_employees)
    pending_count = max(0, total_active - allocated_count)
    completion_pct = round((allocated_count / total_active * 100), 1) if total_active else 0
    total_days = sum(float(r.get("new_leaves_allocated") or 0) for r in allocations)

    emp_names = list(allocated_employees)
    emp_map = {}
    if emp_names:
        emp_data = (
            frappe.qb.from_(Employee)
            .select(Employee.name, Employee.employee_name)
            .where(Employee.name.isin(emp_names))
        ).run(as_dict=True)
        emp_map = {e["name"]: e for e in emp_data}

    detail = []
    for r in allocations:
        e = emp_map.get(r["employee"], {})
        detail.append({
            "accrual_date": str(r.get("creation") or r.get("from_date") or ""),
            "employee": r["employee"],
            "employee_name": e.get("employee_name", ""),
            "leave_type": r.get("leave_type", ""),
            "accrued_days": float(r.get("new_leaves_allocated") or 0),
            "status": "Allocated",
        })

    current_month = frappe.utils.formatdate(current_month_start, "MMMM yyyy")

    return {
        "kpi": {
            "current_month": current_month,
            "processed_employees": allocated_count,
            "pending_employees": pending_count,
            "completion_pct": completion_pct,
            "total_days_allocated": round(total_days, 1),
        },
        "rows": detail,
        "accrual_has_run": allocated_count > 0,
    }


@frappe.whitelist()
@frappe.read_only()
def get_current_month_leave_applications():
    LeaveApplication = frappe.qb.DocType("Leave Application")

    today_date = getdate(frappe.utils.today())
    current_month_start = today_date.replace(day=1)
    from frappe.utils import get_last_day
    month_end = str(get_last_day(current_month_start))

    rows = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.name,
            LeaveApplication.employee,
            LeaveApplication.employee_name,
            LeaveApplication.department,
            LeaveApplication.company,
            LeaveApplication.leave_type,
            LeaveApplication.from_date,
            LeaveApplication.to_date,
            LeaveApplication.total_leave_days,
            LeaveApplication.posting_date,
            LeaveApplication.status,
            LeaveApplication.docstatus,
            LeaveApplication.leave_approver,
            LeaveApplication.custom_approval_status,
            LeaveApplication.workflow_state,
        )
        .where(LeaveApplication.posting_date >= current_month_start)
        .where(LeaveApplication.posting_date <= month_end)
        .orderby(LeaveApplication.posting_date, order=frappe.qb.desc)
        .limit(5000)
    ).run(as_dict=True)

    total = len(rows)
    pending = 0
    approved = 0
    rejected = 0
    cancelled = 0

    detail = []
    for r in rows:
        ds = r.get("docstatus", 0)
        st = (r.get("status") or "").lower()
        wf = (r.get("custom_approval_status") or r.get("workflow_state") or r.get("status") or "Open")

        if ds == 2 or st == "cancelled":
            display_status = "Cancelled"
            cancelled += 1
        elif st == "approved" or ds == 1:
            display_status = "Approved"
            approved += 1
        elif st == "rejected":
            display_status = "Rejected"
            rejected += 1
        else:
            display_status = "Pending"
            pending += 1

        detail.append({
            "name": r["name"],
            "employee": r["employee"],
            "employee_name": r.get("employee_name", ""),
            "department": r.get("department", ""),
            "company": r.get("company", ""),
            "leave_type": r.get("leave_type", ""),
            "from_date": str(r.get("from_date") or ""),
            "to_date": str(r.get("to_date") or ""),
            "total_days": float(r.get("total_leave_days") or 0),
            "posting_date": str(r.get("posting_date") or ""),
            "status": display_status,
            "workflow_state": wf,
            "leave_approver": r.get("leave_approver", ""),
        })

    return {
        "kpi": {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "cancelled": cancelled,
            "current_month": frappe.utils.formatdate(current_month_start, "MMMM yyyy"),
        },
        "rows": detail,
    }


@frappe.whitelist()
@frappe.read_only()
def get_rejoining_overdue():
    from frappe.utils import add_days, date_diff

    today_date = getdate(today())

    LA = frappe.qb.DocType("Leave Application")
    RF = frappe.qb.DocType("Rejoining Form")

    rejoining_sub = (
        frappe.qb.from_(RF)
        .select(RF.leave_application)
        .where((RF.docstatus == 1) & (RF.leave_application.isnotnull()))
    )

    rows = (
        frappe.qb.from_(LA)
        .select(
            LA.name,
            LA.employee,
            LA.employee_name,
            LA.department,
            LA.company,
            LA.leave_type,
            LA.from_date,
            LA.to_date,
            LA.total_leave_days,
            LA.status,
        )
        .where(
            (LA.docstatus == 1)
            & (LA.status.isin(["Submitted", "Approved"]))
            & (LA.to_date < today_date)
            & (LA.name.notin(rejoining_sub))
        )
        .orderby(LA.to_date, order=frappe.qb.asc)
        .limit(5000)
    ).run(as_dict=True)

    detail = []
    total = len(rows)
    bucket_1_7 = 0
    bucket_8_30 = 0
    bucket_30_plus = 0

    for r in rows:
        to_date = getdate(r.get("to_date"))
        expected_rejoining = add_days(to_date, 1)
        overdue_days = date_diff(today_date, to_date)

        if overdue_days <= 7:
            bucket_1_7 += 1
        elif overdue_days <= 30:
            bucket_8_30 += 1
        else:
            bucket_30_plus += 1

        detail.append({
            "employee": r.get("employee", ""),
            "employee_name": r.get("employee_name", ""),
            "name": r.get("name", ""),
            "leave_type": r.get("leave_type", ""),
            "from_date": str(r.get("from_date") or ""),
            "to_date": str(r.get("to_date") or ""),
            "leave_end_date": str(r.get("to_date") or ""),
            "expected_rejoining_date": str(expected_rejoining),
            "overdue_days": overdue_days,
            "department": r.get("department", ""),
            "company": r.get("company", ""),
        })

    return {
        "kpi": {
            "total": total,
            "overdue_1_7": bucket_1_7,
            "overdue_8_30": bucket_8_30,
            "overdue_30_plus": bucket_30_plus,
        },
        "rows": detail,
    }
