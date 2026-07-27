import frappe
from frappe.utils import getdate


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
