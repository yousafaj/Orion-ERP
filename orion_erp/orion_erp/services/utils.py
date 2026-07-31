import frappe


def get_deduction_doctype(reference):
    if frappe.db.exists("Employee Deduction Detail", reference):
        return "Employee Deduction Detail"
    if frappe.db.exists("Outstanding Employee Deduction Detail", reference):
        return "Outstanding Employee Deduction Detail"
    return None


def remove_reference_link(existing_ref, docname):
    if not existing_ref:
        return ""
    refs = [r.strip() for r in existing_ref.split("<br>") if r.strip()]
    cleaned_refs = [r for r in refs if docname not in r]
    return "<br>".join(cleaned_refs)
