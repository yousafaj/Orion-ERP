import frappe
from frappe import _
from frappe.utils import flt


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


@frappe.whitelist()
def get_manual_paid_lock_date():
    return frappe.db.get_single_value(
        "Orion Settings",
        "manual_paid_check_read_only_date"
    )
