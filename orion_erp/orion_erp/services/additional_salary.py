import frappe
from frappe.utils import get_link_to_form, getdate, add_months, get_last_day, nowdate

from orion_erp.orion_erp.services.utils import get_deduction_doctype, remove_reference_link


def autoname(self, method):
    if self.salary_component == "Total Deduction":
        prefix = "HR-ADA-.YY.-.MM.-"
    else:
        prefix = "HR-ADS-.YY.-.MM.-"
    self.name = frappe.model.naming.make_autoname(f"{prefix}.#####")


def validate(self, method):
    if self.salary_component == "Total Deduction":
        total = sum(row.installation_amount or 0 for row in self.custom_penalties_detail)
        self.amount = total


def on_submit(self, method):
    if self.salary_component == "Total Deduction":
        update_deductions(self)
        create_additional_deduction(self)


def on_cancel(self, method):
    cancel_details = get_leave_settlement_cancel_details(self)
    if cancel_details:
        frappe.throw(
            f"Cannot cancel this Additional Salary directly. "
            f"Please cancel the linked Leave Settlement "
            f"<a href='/app/leave-settlement/{cancel_details}'>"
            f"{cancel_details}</a> instead, "
            f"which will automatically cancel this Additional Salary."
        )

    if (
        self.salary_component == "Ticket Allowance"
        and self.custom_auto_generated
        and self.custom_reference_
        and not frappe.flags.ignore_ticket_allowance_validation
    ):
        frappe.throw(
            f"Cannot cancel this Additional Salary directly. "
            f"Please cancel the linked Leave Settlement "
            f"<a href='/app/leave-settlement/{self.custom_reference_}'>"
            f"{self.custom_reference_}</a> instead, "
            f"which will automatically cancel this Additional Salary."
        )

    if self.salary_component == "Total Deduction":
        reverse_deductions(self)


def get_leave_settlement_cancel_details(self):
    if self.ref_doctype == "Leave Encashment" and self.ref_docname:
        leave_settlement_ref = frappe.db.get_value(
            "Leave Encashment", self.ref_docname, "custom_leave_settlement_ref"
        )
        if leave_settlement_ref:
            ls_docstatus = frappe.db.get_value("Leave Settlement", leave_settlement_ref, "docstatus")
            if ls_docstatus == 1:
                return leave_settlement_ref
        else:
            enc_docstatus = frappe.db.get_value("Leave Encashment", self.ref_docname, "docstatus")
            if enc_docstatus == 1:
                return self.ref_docname

    if self.custom_reference_:
        docstatus = frappe.db.get_value("Leave Settlement", self.custom_reference_, "docstatus")
        if docstatus == 1:
            return self.custom_reference_

    return None


def update_deductions(doc):
    if not doc.employee:
        return

    for row in doc.custom_penalties_detail:
        if not row.employee_deduction_reference or not row.installation_amount:
            continue
        _update_single_deduction_row(doc, row)


def _update_single_deduction_row(doc, row):
    doctype = get_deduction_doctype(row.employee_deduction_reference)
    if not doctype:
        frappe.throw(f"Invalid reference: {row.employee_deduction_reference}")

    fields = ["remaining_amount", "paid_amount", "parent", "reference"]
    if doctype == "Outstanding Employee Deduction Detail":
        fields.append("child_ref")

    d = frappe.db.get_value(doctype, row.employee_deduction_reference, fields, as_dict=1)
    if not d:
        return

    deduct = min(row.installation_amount, d.remaining_amount or 0)
    new_paid = (d.paid_amount or 0) + deduct
    new_remaining = (d.remaining_amount or 0) - deduct
    status = "Paid" if new_remaining <= 0 else "Partial Paid"

    updated_reference = _build_updated_reference(d.reference, doc.name)

    frappe.db.set_value(
        doctype, row.employee_deduction_reference,
        {
            "paid_amount": new_paid,
            "remaining_amount": new_remaining,
            "status": status,
            "reference": updated_reference
        }
    )

    parents_to_update = {d.parent}

    if doctype == "Outstanding Employee Deduction Detail" and d.get("child_ref"):
        _sync_child_row(d.child_ref, new_paid, new_remaining, status, updated_reference)
        original_parent = frappe.db.get_value("Employee Deduction Detail", d.child_ref, "parent")
        if original_parent:
            parents_to_update.add(original_parent)

    for p in parents_to_update:
        update_parent_totals(p)


def _build_updated_reference(existing_ref, docname):
    link = get_link_to_form("Additional Salary", docname)
    refs = [r.strip() for r in (existing_ref or "").split("<br>") if r.strip()]
    if link not in refs:
        refs.append(link)
    return "<br>".join(refs)


def _sync_child_row(child_ref, new_paid, new_remaining, status, reference):
    frappe.db.set_value(
        "Employee Deduction Detail", child_ref,
        {
            "paid_amount": new_paid,
            "remaining_amount": new_remaining,
            "status": status,
            "reference": reference
        }
    )


def update_parent_totals(parent):
    data = frappe.db.sql("""
        SELECT
            SUM(deduction_amount) as total,
            SUM(paid_amount) as paid,
            SUM(remaining_amount) as remaining,
            COUNT(*) as total_rows,
            SUM(CASE WHEN status = 'Paid' THEN 1 ELSE 0 END) as paid_rows,
            SUM(CASE WHEN status = 'Unpaid' THEN 1 ELSE 0 END) as unpaid_rows
        FROM (
            SELECT deduction_amount, paid_amount, remaining_amount, status
            FROM `tabEmployee Deduction Detail`
            WHERE parent = %(parent)s
            UNION ALL
            SELECT deduction_amount, paid_amount, remaining_amount, status
            FROM `tabOutstanding Employee Deduction Detail`
            WHERE parent = %(parent)s
        ) t
    """, {"parent": parent}, as_dict=1)[0]

    status = _compute_deduction_status(
        data.total_rows or 0,
        data.paid_rows or 0,
        data.unpaid_rows or 0
    )

    frappe.db.set_value("Employee Deduction", parent, {
        "total_deduction": data.total or 0,
        "paid_amount": data.paid or 0,
        "remaining_balance": data.remaining or 0,
        "status": status
    })


def _compute_deduction_status(total_rows, paid_rows, unpaid_rows):
    if total_rows == 0:
        return "Draft"
    elif paid_rows == total_rows:
        return "Paid"
    elif unpaid_rows == total_rows:
        return "Unpaid"
    return "Partial Paid"


def reverse_deductions(doc):
    if not doc.employee:
        return

    parents_to_update_all = set()

    for row in doc.custom_penalties_detail:
        if not row.employee_deduction_reference or not row.installation_amount:
            continue
        parents = _reverse_single_deduction_row(doc, row)
        parents_to_update_all.update(parents)

    for p in parents_to_update_all:
        update_parent_totals(p)

    clean_latest_outstanding_refs(doc)


def _reverse_single_deduction_row(doc, row):
    doctype = get_deduction_doctype(row.employee_deduction_reference)
    if not doctype:
        return set()

    fields = ["remaining_amount", "paid_amount", "parent", "reference"]
    if doctype == "Outstanding Employee Deduction Detail":
        fields.append("child_ref")

    d = frappe.db.get_value(doctype, row.employee_deduction_reference, fields, as_dict=1)
    if not d:
        return set()

    reverse = row.installation_amount
    parents_to_update = set()

    _update_main_row_for_reverse(doctype, row.employee_deduction_reference, d, reverse, doc.name)

    if doctype == "Outstanding Employee Deduction Detail" and d.get("child_ref"):
        parents = _reverse_child_row(d, reverse, doc.name)
        parents_to_update.update(parents)

    if doctype == "Employee Deduction Detail":
        parents = _reverse_outstanding_row(row.employee_deduction_reference, reverse, doc.name)
        parents_to_update.update(parents)

    parents_to_update.add(d.parent)
    return parents_to_update


def _update_main_row_for_reverse(doctype, ref_name, d, reverse, doc_name):
    new_paid = max((d.paid_amount or 0) - reverse, 0)
    new_remaining = (d.remaining_amount or 0) + reverse
    status = _compute_payment_status(new_paid, new_remaining)
    updated_reference = remove_reference_link(d.reference, doc_name)

    frappe.db.set_value(
        doctype, ref_name,
        {
            "paid_amount": new_paid,
            "remaining_amount": new_remaining,
            "status": status,
            "reference": updated_reference
        }
    )


def _compute_payment_status(paid, remaining):
    if paid == 0:
        return "Unpaid"
    elif remaining == 0:
        return "Paid"
    return "Partial Paid"


def _reverse_child_row(d, reverse, doc_name):
    child = frappe.db.get_value(
        "Employee Deduction Detail", d.child_ref,
        ["paid_amount", "remaining_amount", "reference", "parent"],
        as_dict=True
    )
    if not child:
        return set()

    c_new_paid = max((child.paid_amount or 0) - reverse, 0)
    c_new_remaining = (child.remaining_amount or 0) + reverse
    c_status = _compute_payment_status(c_new_paid, c_new_remaining)
    c_updated_ref = remove_reference_link(child.reference, doc_name)

    frappe.db.set_value(
        "Employee Deduction Detail", d.child_ref,
        {
            "paid_amount": c_new_paid,
            "remaining_amount": c_new_remaining,
            "status": c_status,
            "reference": c_updated_ref
        },
        update_modified=False
    )
    return {child.parent}


def _reverse_outstanding_row(child_ref, reverse, doc_name):
    outstanding_rows = frappe.db.sql("""
        SELECT name, paid_amount, remaining_amount, parent, reference
        FROM `tabOutstanding Employee Deduction Detail`
        WHERE child_ref = %s
        ORDER BY creation DESC
        LIMIT 1
    """, (child_ref,), as_dict=True)

    if not outstanding_rows:
        return set()

    o = outstanding_rows[0]
    o_new_paid = max((o.paid_amount or 0) - reverse, 0)
    o_new_remaining = (o.remaining_amount or 0) + reverse
    o_status = _compute_payment_status(o_new_paid, o_new_remaining)
    o_updated_ref = remove_reference_link(o.reference, doc_name)

    frappe.db.set_value(
        "Outstanding Employee Deduction Detail", o.name,
        {
            "paid_amount": o_new_paid,
            "remaining_amount": o_new_remaining,
            "status": o_status,
            "reference": o_updated_ref
        }
    )
    return {o.parent}


def create_additional_deduction(doc):
    if doc.salary_component != "Total Deduction" or not doc.employee:
        return

    if frappe.db.exists("Additional Deduction", {
        "ref_doctype": "Additional Salary",
        "ref_docname": doc.name,
        "docstatus": 1
    }):
        return

    ad = _build_additional_deduction_doc(doc)
    ad.insert(ignore_permissions=True)
    ad.submit()
    _link_deduction_refs(ad, doc)


def _build_additional_deduction_doc(doc):
    ad = frappe.new_doc("Additional Deduction")
    ad.employee = doc.employee
    ad.company = doc.company
    ad.payroll_date = doc.payroll_date
    ad.salary_component = doc.salary_component
    ad.amount = doc.amount
    ad.process_employee_deduction_ref = doc.custom_reference_
    ad.ref_doctype = "Additional Salary"
    ad.ref_docname = doc.name

    for row in doc.custom_penalties_detail or []:
        child = ad.append("additional_deduction_detail", {})
        child.penalty_name = row.penalty_name
        child.installation_amount = row.installation_amount
        child.employee_deduction_reference = row.employee_deduction_reference
        child.date_of_deduction_occurred = row.date_of_deduction_occurred
        child.remaining_amount = row.remaining_amount
        child.remarks = row.remarks

    return ad


def _link_deduction_refs(ad, doc):
    for row in doc.custom_penalties_detail or []:
        if not row.employee_deduction_reference:
            continue

        doctype = get_deduction_doctype(row.employee_deduction_reference)
        if not doctype:
            continue

        existing_ref = frappe.db.get_value(
            doctype, row.employee_deduction_reference, "additional_deduction_ref"
        ) or ""

        link = get_link_to_form("Additional Deduction", ad.name)
        refs = [r.strip() for r in existing_ref.split("<br>") if r.strip()]
        refs = [r for r in refs if ad.name not in r]
        refs.append(link)

        frappe.db.set_value(
            doctype, row.employee_deduction_reference,
            "additional_deduction_ref", "<br>".join(refs),
            update_modified=False
        )

    return ad


def clean_latest_outstanding_refs(doc):
    if not doc.employee:
        return

    like_pattern = f"%{doc.name}%"
    rows = frappe.db.sql("""
        SELECT name, reference
        FROM `tabOutstanding Employee Deduction Detail`
        WHERE reference LIKE %s
        ORDER BY creation DESC
        LIMIT 1
    """, (like_pattern,), as_dict=True)

    for r in rows:
        new_ref = remove_reference_link(r.reference, doc.name)
        frappe.db.set_value(
            "Outstanding Employee Deduction Detail", r.name,
            {"reference": new_ref}, update_modified=False
        )


def create_monthly_allowances():
    today_date = getdate(nowdate())
    last_month_date = add_months(today_date, -1)
    start_date = last_month_date.replace(day=1)
    end_date = get_last_day(last_month_date)

    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=[
            "name", "employee_name", "company",
            "custom_site_allowances", "custom_site_allowances_amount",
            "custom_offshore_allowances", "custom_offshore_allowances_amount",
        ],
    )

    for emp in employees:
        _create_allowance_for_component(
            emp, "Site Allowances", emp.custom_site_allowances,
            emp.custom_site_allowances_amount, start_date, end_date
        )
        _create_allowance_for_component(
            emp, "Offshore Allowances", emp.custom_offshore_allowances,
            emp.custom_offshore_allowances_amount, start_date, end_date
        )


def _create_allowance_for_component(emp, component, is_enabled, amount, start_date, end_date):
    if not is_enabled or not amount:
        return
    try:
        create_additional_salary_for_allowance(
            emp, component=component, amount=amount,
            payroll_date=end_date, start_date=start_date, end_date=end_date
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"{component} Failed for {emp.name}"
        )


def create_additional_salary_for_allowance(emp, component, amount, payroll_date, start_date, end_date):
    exists = frappe.db.exists(
        "Additional Salary",
        {
            "employee": emp.name,
            "salary_component": component,
            "payroll_date": payroll_date,
            "docstatus": 1
        }
    )
    if exists:
        return

    doc = frappe.get_doc({
        "doctype": "Additional Salary",
        "employee": emp.name,
        "employee_name": emp.employee_name,
        "company": emp.company,
        "salary_component": component,
        "amount": amount,
        "payroll_date": payroll_date,
        "from_date": start_date,
        "to_date": end_date,
    })
    doc.insert(ignore_permissions=True)
    doc.submit()
