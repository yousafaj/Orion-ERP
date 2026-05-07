import frappe
import json
from frappe.utils import get_link_to_form,getdate, add_months, get_last_day, nowdate

def validate(self, method):
    if self.salary_component == "Total Deduction":
        total = 0

        for row in self.custom_penalties_detail:
            total += row.installation_amount or 0

        self.amount = total


def on_submit(self,method):
        # Apply deduction when salary is submitted
        if self.salary_component == "Total Deduction":
            update_deductions(self)
            create_additional_deduction(self)

def on_cancel(self,method):
        # Reverse deduction when salary is cancelled
        if self.salary_component == "Total Deduction":
            reverse_deductions(self)



def get_deduction_doctype(reference):

    if frappe.db.exists("Employee Deduction Detail", reference):
        return "Employee Deduction Detail"

    if frappe.db.exists("Outstanding Employee Deduction Detail", reference):
        return "Outstanding Employee Deduction Detail"

    return None

def update_deductions(doc):

    if not doc.employee:
        return

    for row in doc.custom_penalties_detail:

        if not row.employee_deduction_reference or not row.installation_amount:
            continue

        doctype = get_deduction_doctype(row.employee_deduction_reference)

        if not doctype:
            frappe.throw(f"Invalid reference: {row.employee_deduction_reference}")

        fields = ["remaining_amount", "paid_amount", "parent", "reference"]

        if doctype == "Outstanding Employee Deduction Detail":
            fields.append("child_ref")

        d = frappe.db.get_value(
            doctype,
            row.employee_deduction_reference,
            fields,
            as_dict=1
        )

    

        if not d:
            continue

        deduct = min(row.installation_amount, d.remaining_amount or 0)

        new_paid = (d.paid_amount or 0) + deduct
        new_remaining = (d.remaining_amount or 0) - deduct

        status = "Paid" if new_remaining <= 0 else "Partial Paid"

        link = get_link_to_form("Additional Salary", doc.name)

        existing_ref = d.reference or ""
        refs = [r.strip() for r in existing_ref.split("<br>") if r.strip()]

        if link not in refs:
            refs.append(link)

        updated_reference = "<br>".join(refs)

        frappe.db.set_value(
            doctype,
            row.employee_deduction_reference,
            {
                "paid_amount": new_paid,
                "remaining_amount": new_remaining,
                "status": status,
                "reference": updated_reference
            }
        )
        parents_to_update = {d.parent}

        if doctype == "Outstanding Employee Deduction Detail" and d.get("child_ref"):
            frappe.db.set_value(
                "Employee Deduction Detail",
                d.child_ref,
                {
                    "paid_amount": new_paid,
                    "remaining_amount": new_remaining,
                    "status": status,
                    "reference": updated_reference
                }
            )
        
            original_parent = frappe.db.get_value(
                "Employee Deduction Detail",
                d.child_ref,
                "parent"
            )

            if original_parent:
                parents_to_update.add(original_parent)
        for p in parents_to_update:
            update_parent_totals(p)


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

    total = data.total or 0
    paid = data.paid or 0
    remaining = data.remaining or 0

    total_rows = data.total_rows or 0
    paid_rows = data.paid_rows or 0
    unpaid_rows = data.unpaid_rows or 0

    if total_rows == 0:
        status = "Draft"
    elif paid_rows == total_rows:
        status = "Paid"
    elif unpaid_rows == total_rows:
        status = "Unpaid"
    else:
        status = "Partial Paid"

    frappe.db.set_value("Employee Deduction", parent, {
        "total_deduction": total,
        "paid_amount": paid,
        "remaining_balance": remaining,
        "status": status
    })


def remove_reference_link(existing_ref, docname):

    if not existing_ref:
        return ""

    refs = [r.strip() for r in existing_ref.split("<br>") if r.strip()]

    cleaned_refs = [r for r in refs if docname not in r]

    return "<br>".join(cleaned_refs)

def reverse_deductions(doc):

    if not doc.employee:
        return

    parents_to_update_all = set()

    for row in doc.custom_penalties_detail:

        if not row.employee_deduction_reference or not row.installation_amount:
            continue

        doctype = get_deduction_doctype(row.employee_deduction_reference)
        if not doctype:
            continue

        fields = ["remaining_amount", "paid_amount", "parent", "reference"]

        if doctype == "Outstanding Employee Deduction Detail":
            fields.append("child_ref")

        d = frappe.db.get_value(
            doctype,
            row.employee_deduction_reference,
            fields,
            as_dict=1
        )

        if not d:
            continue

        reverse = row.installation_amount

        # MAIN ROW UPDATE
        new_paid = max((d.paid_amount or 0) - reverse, 0)
        new_remaining = (d.remaining_amount or 0) + reverse

        if new_paid == 0:
            status = "Unpaid"
        elif new_remaining == 0:
            status = "Paid"
        else:
            status = "Partial Paid"

        updated_reference = remove_reference_link(d.reference, doc.name)

        frappe.db.set_value(
            doctype,
            row.employee_deduction_reference,
            {
                "paid_amount": new_paid,
                "remaining_amount": new_remaining,
                "status": status,
                "reference": updated_reference
            }
        )

        parents_to_update = {d.parent}

        # CASE 1: OUTSTANDING → UPDATE CHILD
        if doctype == "Outstanding Employee Deduction Detail" and d.get("child_ref"):

            child = frappe.db.get_value(
                "Employee Deduction Detail",
                d.child_ref,
                ["paid_amount", "remaining_amount", "reference", "parent"],
                as_dict=True
            )

            if child:

                c_new_paid = max((child.paid_amount or 0) - reverse, 0)
                c_new_remaining = (child.remaining_amount or 0) + reverse

                if c_new_paid == 0:
                    c_status = "Unpaid"
                elif c_new_remaining == 0:
                    c_status = "Paid"
                else:
                    c_status = "Partial Paid"

                c_updated_ref = remove_reference_link(child.reference, doc.name)

                frappe.db.set_value(
                    "Employee Deduction Detail",
                    d.child_ref,
                    {
                        "paid_amount": c_new_paid,
                        "remaining_amount": c_new_remaining,
                        "status": c_status,
                        "reference": c_updated_ref
                    },
                    update_modified=False
                )

                parents_to_update.add(child.parent)

        # CASE 2: EMPLOYEE → UPDATE LATEST OUTSTANDING
        if doctype == "Employee Deduction Detail":

            outstanding_rows = frappe.db.sql("""
                SELECT name, paid_amount, remaining_amount, parent, reference
                FROM `tabOutstanding Employee Deduction Detail`
                WHERE child_ref = %s
                ORDER BY creation DESC
                LIMIT 1
            """, (row.employee_deduction_reference,), as_dict=True)

            if outstanding_rows:
                o = outstanding_rows[0]

                o_new_paid = max((o.paid_amount or 0) - reverse, 0)
                o_new_remaining = (o.remaining_amount or 0) + reverse

                if o_new_paid == 0:
                    o_status = "Unpaid"
                elif o_new_remaining == 0:
                    o_status = "Paid"
                else:
                    o_status = "Partial Paid"

                o_updated_ref = remove_reference_link(o.reference, doc.name)

                frappe.db.set_value(
                    "Outstanding Employee Deduction Detail",
                    o.name,
                    {
                        "paid_amount": o_new_paid,
                        "remaining_amount": o_new_remaining,
                        "status": o_status,
                        "reference": o_updated_ref
                    }
                )

                parents_to_update.add(o.parent)

        parents_to_update_all.update(parents_to_update)

    # UPDATE PARENT TOTALS ONCE
    for p in parents_to_update_all:
        update_parent_totals(p)

    clean_latest_outstanding_refs(doc)


def create_additional_deduction(doc):

    if doc.salary_component != "Total Deduction":
        return

    if not doc.employee:
        return

    if frappe.db.exists("Additional Deduction", {
        "ref_doctype": "Additional Salary",
        "ref_docname": doc.name,
        "docstatus": 1
    }):
        return

    ad = frappe.new_doc("Additional Deduction")

    # -------- Parent --------
    ad.employee = doc.employee
    ad.company = doc.company
    ad.payroll_date = doc.payroll_date
    ad.salary_component = doc.salary_component
    ad.amount = doc.amount

    ad.ref_doctype = "Additional Salary"
    ad.ref_docname = doc.name

    # -------- Child --------
    for row in doc.custom_penalties_detail or []:

        child = ad.append("additional_deduction_detail", {})

        child.penalty_name = row.penalty_name
        child.installation_amount = row.installation_amount
        child.employee_deduction_reference = row.employee_deduction_reference
        child.date_of_deduction_occurred = row.deduction_date
        child.remaining_amount = row.remaining_amount
        child.remarks = row.remarks

    ad.insert(ignore_permissions=True)
    ad.submit()


    for row in doc.custom_penalties_detail or []:

        if not row.employee_deduction_reference:
            continue

        doctype = get_deduction_doctype(row.employee_deduction_reference)
        if not doctype:
            continue

        existing_ref = frappe.db.get_value(
            doctype,
            row.employee_deduction_reference,
            "additional_deduction_ref"
        ) or ""

        link = get_link_to_form("Additional Deduction", ad.name)

        refs = [r.strip() for r in existing_ref.split("<br>") if r.strip()]

        refs = [r for r in refs if ad.name not in r]

        refs.append(link)

        updated_ref = "<br>".join(refs)

        frappe.db.set_value(
            doctype,
            row.employee_deduction_reference,
            "additional_deduction_ref",
            updated_ref,
            update_modified=False
        )

    return ad

def autoname(self,method):

    if self.salary_component == "Total Deduction":
        prefix = "HR-ADA-.YY.-.MM.-"
    else:
        prefix = "HR-ADS-.YY.-.MM.-"

    self.name = frappe.model.naming.make_autoname(
        f"{prefix}.#####"
    )

def clean_latest_outstanding_refs(doc):

    if not doc.employee:
        return

    like_pattern = f"%{doc.name}%"

    
    # GET LATEST OUTSTANDING ROW FOR THIS REF
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
            "Outstanding Employee Deduction Detail",
            r.name,
            {
                "reference": new_ref
            },
            update_modified=False
        )


def create_monthly_allowances():
    today = getdate(nowdate())

    # Get last month start & end
    last_month_date = add_months(today, -1)
    start_date = last_month_date.replace(day=1)
    end_date = get_last_day(last_month_date)

    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=[
            "name",
            "employee_name",
            "company",
            "custom_site_allowances",
            "custom_site_allowances_amount",
            "custom_offshore_allowances",
            "custom_offshore_allowances_amount",
        ],
    )

    for emp in employees:

        # ---------- SITE ALLOWANCE ----------
        if emp.custom_site_allowances and emp.custom_site_allowances_amount:
            try:
                create_additional_salary(
                    emp,
                    component="Site Allowances",
                    amount=emp.custom_site_allowances_amount,
                    payroll_date=end_date,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Site Allowance Failed for {emp.name}"
                )

        # ---------- OFFSHORE ALLOWANCE ----------
        if emp.custom_offshore_allowances and emp.custom_offshore_allowances_amount:
            try:
                create_additional_salary(
                    emp,
                    component="Offshore Allowances",
                    amount=emp.custom_offshore_allowances_amount,
                    payroll_date=end_date,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Offshore Allowance Failed for {emp.name}"
                )


def create_additional_salary(emp, component, amount, payroll_date, start_date, end_date):

    # Prevent duplicate creation
    exists = frappe.db.exists(
        "Additional Salary",
        {
            "employee": emp.name,
            "salary_component": component,
            "payroll_date": payroll_date,
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