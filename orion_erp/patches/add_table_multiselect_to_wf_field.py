import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
    if not frappe.db.exists("DocType", "Web Form Field"):
        return

    current_options = frappe.db.get_value(
        "DocField",
        {"parent": "Web Form Field", "fieldname": "fieldtype"},
        "options",
    )
    if not current_options or "Table MultiSelect" in current_options:
        return

    new_options = current_options + "\nTable MultiSelect"
    make_property_setter(
        "Web Form Field",
        "fieldtype",
        "options",
        new_options,
        "Text",
    )
    frappe.db.commit()
