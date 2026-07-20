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

    exists = frappe.db.exists(
        "Ticket Allowance Detail",
        {
            "parent": emp.name,
            "parenttype": "Employee",
            "from_date": from_date
        }
    )
    if exists:
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
    total_days = (to_date - from_date).days + 1
    if total_days <= 0:
        return

    days_elapsed = (getdate(today_date) - from_date).days + 1
    days_elapsed = min(days_elapsed, total_days)
    pro_rata = (flt(current_cycle.amount) / total_days) * days_elapsed

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
    if not doc.custom_leave_policy or not doc.date_of_joining:
        return

    existing = frappe.db.exists("Leave Policy Assignment", {
        "employee": doc.name,
        "leave_policy": doc.custom_leave_policy,
        "docstatus": ["!=", 2]
    })
    if existing:
        return

    effective_from, effective_to = _get_effective_period(doc.date_of_joining)
    _validate_no_conflicting_allocations(doc, effective_from, effective_to)
    _create_and_submit_lpa(doc, effective_from, effective_to)


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


def _validate_no_conflicting_allocations(doc, effective_from, effective_to):
    leave_policy = frappe.get_doc("Leave Policy", doc.custom_leave_policy)
    conflicting = []

    for detail in leave_policy.leave_policy_details:
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


def _create_and_submit_lpa(doc, effective_from, effective_to):
    lpa = frappe.new_doc("Leave Policy Assignment")
    lpa.employee = doc.name
    lpa.leave_policy = doc.custom_leave_policy
    lpa.assignment_based_on = "Joining Date"
    lpa.effective_from = effective_from
    lpa.effective_to = effective_to
    lpa.carry_forward = 0
    lpa.insert(ignore_permissions=True)
    lpa.submit()


def auto_renew_leave_policy_assignments():
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active", "custom_leave_policy": ["!=", ""]},
        fields=["name", "company", "date_of_joining", "custom_leave_policy"]
    )
    today_date = getdate()

    for emp in employees:
        effective_from, effective_to = _get_effective_period(emp.date_of_joining)
        _renew_single_employee_lpa(emp, effective_from, effective_to)


def _renew_single_employee_lpa(emp, effective_from, effective_to):
    exists = frappe.db.exists("Leave Policy Assignment", {
        "employee": emp.name,
        "leave_policy": emp.custom_leave_policy,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "docstatus": 1
    })
    if exists:
        return

    lpa = frappe.new_doc("Leave Policy Assignment")
    lpa.employee = emp.name
    lpa.leave_policy = emp.custom_leave_policy
    lpa.assignment_based_on = "Joining Date"
    lpa.effective_from = effective_from
    lpa.effective_to = effective_to
    lpa.carry_forward = 0
    lpa.insert(ignore_permissions=True)
    lpa.submit()


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
    leave_type_name = "HAJI/ UMRAH LEAVE"
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
