import frappe
from frappe import _
from frappe.utils import cint

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

    limit = cint(limit) if limit is not None else None
    offset = cint(offset) if offset is not None else None

    employees = get_employee_list(
        filters=filters,
        searchfield=filters.get("searchfield"),
        search_string=filters.get("txt"),
        fields=["employee", "employee_name", "department", "designation"],
        as_dict=True,
        limit=limit,
        offset=offset,
        ignore_match_conditions=True,
    )

    withheld = set(
        get_salary_withholdings(
            start_date=filters.start_date,
            end_date=filters.end_date,
            pluck="employee",
        )
    )
    for e in employees:
        e["is_salary_withheld"] = 1 if e.get("employee") in withheld else 0

    post_filters = {
        "employment_type": filters.get("employment_type"),
        "location": filters.get("location"),
        "project": filters.get("project"),
    }
    if any(post_filters.values()):
        emp_ids = [e["employee"] for e in employees]
        if emp_ids:
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
