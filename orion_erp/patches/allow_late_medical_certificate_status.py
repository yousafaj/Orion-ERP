"""Permit the computed certificate status to follow late attachment updates."""

import frappe


def execute():
    for fieldname in ("custom_medical_certificate", "custom_medical_certificate_status"):
        name = frappe.db.get_value("Custom Field", {
            "dt": "Leave Application", "fieldname": fieldname,
        }, "name")
        if name:
            frappe.db.set_value("Custom Field", name, "allow_on_submit", 1)
    frappe.clear_cache(doctype="Leave Application")
