import frappe
from frappe.utils import get_link_to_form

from orion_erp.orion_erp.services.utils import get_deduction_doctype, remove_reference_link


def cancel_additional_salary_from_deduction(self):
    salary_list = frappe.get_all(
        "Additional Salary",
        filters={"ref_doctype": "Additional Deduction", "ref_docname": self.name},
        pluck="name"
    )

    for sal_name in salary_list:
        if not frappe.db.exists("Additional Salary", sal_name):
            continue
        sal_doc = frappe.get_doc("Additional Salary", sal_name)
        if sal_doc.docstatus == 1:
            sal_doc.cancel()


def update_additional_deduction_ref(self):
    link = get_link_to_form("Additional Deduction", self.name)

    for row in self.additional_deduction_detail or []:
        if not row.employee_deduction_reference:
            continue

        doctype = get_deduction_doctype(row.employee_deduction_reference)
        if not doctype:
            continue

        existing = frappe.db.get_value(
            doctype, row.employee_deduction_reference, "additional_deduction_ref"
        ) or ""

        refs = [r.strip() for r in existing.split("<br>") if r.strip()]
        refs = [r for r in refs if "additional-salary" not in r]

        if link not in refs:
            refs.append(link)

        updated = "<br>".join(refs)

        frappe.db.set_value(
            doctype, row.employee_deduction_reference,
            "additional_deduction_ref", updated,
            update_modified=False
        )

        if doctype == "Outstanding Employee Deduction Detail":
            _sync_child_additional_deduction_ref(row, updated)


def _sync_child_additional_deduction_ref(row, updated):
    child_ref = frappe.db.get_value(
        "Outstanding Employee Deduction Detail",
        row.employee_deduction_reference,
        "child_ref"
    )
    if child_ref:
        frappe.db.set_value(
            "Employee Deduction Detail", child_ref,
            "additional_deduction_ref", updated,
            update_modified=False
        )


def remove_additional_deduction_ref(self):
    for row in self.additional_deduction_detail or []:
        if not row.employee_deduction_reference:
            continue

        doctype = get_deduction_doctype(row.employee_deduction_reference)
        if not doctype:
            continue

        existing = frappe.db.get_value(
            doctype, row.employee_deduction_reference, "additional_deduction_ref"
        )
        if not existing:
            continue

        updated = remove_reference_link(existing, self.name)

        frappe.db.set_value(
            doctype, row.employee_deduction_reference,
            "additional_deduction_ref", updated,
            update_modified=False
        )

        if doctype == "Outstanding Employee Deduction Detail":
            _remove_outstanding_child_ref(row, updated)

        if doctype == "Employee Deduction Detail":
            _remove_latest_outstanding_ref(row, self.name)


def _remove_outstanding_child_ref(row, updated):
    child_ref = frappe.db.get_value(
        "Outstanding Employee Deduction Detail",
        row.employee_deduction_reference,
        "child_ref"
    )
    if child_ref:
        frappe.db.set_value(
            "Employee Deduction Detail", child_ref,
            "additional_deduction_ref", updated,
            update_modified=False
        )


def _remove_latest_outstanding_ref(row, doc_name):
    outstanding_rows = frappe.db.sql("""
        SELECT name, additional_deduction_ref
        FROM `tabOutstanding Employee Deduction Detail`
        WHERE child_ref = %s
        OR additional_deduction_ref LIKE %s
        ORDER BY creation DESC
        LIMIT 1
    """, (row.name, f"%{doc_name}%"), as_dict=True)

    if outstanding_rows:
        o = outstanding_rows[0]
        if o.additional_deduction_ref:
            updated_out = remove_reference_link(o.additional_deduction_ref, doc_name)
            frappe.db.set_value(
                "Outstanding Employee Deduction Detail", o.name,
                "additional_deduction_ref", updated_out,
                update_modified=False
            )
