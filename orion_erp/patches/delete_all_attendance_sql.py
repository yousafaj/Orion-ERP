import frappe

def execute():
    frappe.db.sql("DELETE FROM `tabAttendance`")
    frappe.db.commit()