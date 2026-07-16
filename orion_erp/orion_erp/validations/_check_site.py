import frappe
frappe.connect("site2.local")
companies = frappe.db.get_all("Company", pluck="name", limit=5)
print("COMPANIES:", companies)
employees = frappe.db.get_all("Employee", filters={"status": "Active"}, pluck="name", limit=3)
print("EMPLOYEES:", employees)
users = frappe.db.get_all("User", filters={"enabled": 1}, pluck="name", limit=3)
print("USERS:", users)
