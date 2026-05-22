import frappe

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


# rental_management/api.py

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
    Server API for fetching employees for Payroll Entry via rental_management.
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
    
    frappe.errprint(f"this is filters in my func : {filters}")

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
