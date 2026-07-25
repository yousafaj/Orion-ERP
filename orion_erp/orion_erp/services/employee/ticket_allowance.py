import frappe
from frappe import _
from frappe.utils import today, add_days, flt, getdate, add_months


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


def _correct_ticket_allowance_dates(employee, old_doj, new_doj):
    """When DOJ changes, delete ALL existing ticket allowance rows and
    recreate cycles from the new DOJ, preserving amounts from old rows
    that overlap each new cycle."""
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

    rows = frappe.get_all(
        "Ticket Allowance Detail",
        filters={
            "parent": employee,
            "parenttype": "Employee",
        },
        fields=["name", "from_date", "to_date", "amount", "paid", "paid_amount",
                "outstanding_amount", "pro_rata_amount", "idx"],
        order_by="idx asc"
    )

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
    while current_start <= today_date:
        to_date = add_days(add_months(current_start, cycle_months), -1)

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
