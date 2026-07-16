import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from frappe.utils import getdate, today, flt

@frappe.whitelist()
def get_company_logo():
	"""Return company logo from Orion Settings as a base64 data URI.
	Works with S3-stored logos and bypasses permission checks."""
	import base64
	from urllib.parse import parse_qs, urlparse

	logo_url = frappe.db.get_value("Orion Settings", None, "company_logo")
	if not logo_url:
		return ""

	try:
		query = parse_qs(urlparse(logo_url).query)
		key = query.get("key", [None])[0]

		if key:
			s3_settings = frappe.get_single("S3 File Attachment")
			import boto3

			s3 = boto3.client(
				"s3",
				aws_access_key_id=s3_settings.aws_key,
				aws_secret_access_key=s3_settings.get_password("aws_secret"),
				region_name=s3_settings.region_name,
			)
			response = s3.get_object(Bucket=s3_settings.bucket_name, Key=key)
			image_bytes = response["Body"].read()
			ext = key.rsplit(".", 1)[-1].lower()
			mime_map = {
				"png": "image/png",
				"jpg": "image/jpeg",
				"jpeg": "image/jpeg",
				"gif": "image/gif",
				"svg": "image/svg+xml",
			}
			mime = mime_map.get(ext, "image/png")
			return f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
		else:
			return logo_url
	except Exception:
		return logo_url

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
        fields=["leave_type", "from_date", "to_date"]
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
            today(),
            consider_all_leaves_in_the_allocation_period=True
        )

        data.append({
            "leave_type": row.leave_type,
            "balance": balance,
            "from_date": row.from_date,
            "to_date": row.to_date,
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
        ["name", "employee_name", "date_of_joining"],
        as_dict=True,
    )
    if not employee:
        return []

    doj = employee.date_of_joining
    if not doj:
        return []

    if isinstance(doj, str):
        doj = getdate(doj)

    today = frappe.utils.getdate()
    prev_year = doj.year

    from orion_erp.orion_erp.scripts.annual_leave_accrual import get_completed_months

    completed_months = get_completed_months(doj, today)

    if completed_months >= 12:
        current_year_num = completed_months // 12
        prev_year = doj.year + current_year_num - 1

    import re
    cf_pattern = re.compile(
        r'Carry Forward Year\s+\d+\s*\|\s*Carry Forward:\s*([\d.]+)\s*days'
    )

    allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee.name,
            "docstatus": 1,
            "description": ["like", "%Carry Forward%"],
        },
        fields=["leave_type", "description", "total_leaves_allocated",
                "custom_carry_forward_days"],
    )

    result_map = {}
    for alloc in allocations:
        if flt(alloc.total_leaves_allocated) <= 0 and flt(alloc.custom_carry_forward_days) <= 0:
            continue
        if not alloc.description:
            continue
        matches = cf_pattern.findall(alloc.description)
        for match in matches:
            base_cf = float(match)
            approved_excess = float(alloc.custom_carry_forward_days or 0)
            total_cf = base_cf + approved_excess
            lt = alloc.leave_type
            result_map[lt] = result_map.get(lt, 0) + total_cf

    result = [
        {"leave_type": lt, "carry_forward_days": round(days, 1)}
        for lt, days in result_map.items()
    ]
    result.sort(key=lambda x: x["leave_type"])
    return {"prev_year": prev_year, "data": result}


# ---------------------------------------------------------------------------
# HR User Dashboard APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
@frappe.read_only()
def get_org_leave_summary():
    """Organisation-wide Leave Summary with KPIs and detail table."""
    Employee = frappe.qb.DocType("Employee")
    LeaveAllocation = frappe.qb.DocType("Leave Allocation")
    LeaveLedger = frappe.qb.DocType("Leave Ledger Entry")

    today_date = frappe.utils.today()

    total_employees = frappe.db.count("Employee", filters={"status": "Active"})

    # Active allocations valid today
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

    # Get actual net balances from Leave Ledger (sum includes consumption)
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
    """Employees currently on approved leave."""
    LeaveApplication = frappe.qb.DocType("Leave Application")
    Employee = frappe.qb.DocType("Employee")
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
    """Leave applications pending approval longer than 48 hours."""
    LeaveApplication = frappe.qb.DocType("Leave Application")
    Employee = frappe.qb.DocType("Employee")
    today_date = frappe.utils.today()

    from frappe.utils import get_datetime, now_datetime

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
        created = get_datetime(r["creation"])
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
    """Sick leave applications without medical certificates."""
    LeaveApplication = frappe.qb.DocType("Leave Application")
    Employee = frappe.qb.DocType("Employee")

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
    """Leave encashment requests awaiting processing."""
    Encashment = frappe.qb.DocType("Leave Encashment")
    Employee = frappe.qb.DocType("Employee")

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
    """Complete overview of every leave application currently pending."""
    LeaveApplication = frappe.qb.DocType("Leave Application")
    Employee = frappe.qb.DocType("Employee")
    today_date = frappe.utils.today()

    from frappe.utils import get_datetime, now_datetime
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
        created = get_datetime(r["creation"])
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
    """Employees allocated Annual Leave in the current month."""
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

    # Annual Leave allocations effective this month
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


# ---------------------------------------------------------------------------
# Current Month Leave Applications Dashboard
# ---------------------------------------------------------------------------

@frappe.whitelist()
@frappe.read_only()
def get_current_month_leave_applications():
    """All leave applications raised during the current month with KPIs."""
    LeaveApplication = frappe.qb.DocType("Leave Application")
    Employee = frappe.qb.DocType("Employee")

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
