import frappe
from frappe import _

@frappe.whitelist()
def get_company_address_string(company_name):
	if not company_name:
		return ""

	# Get first linked Address via Dynamic Link
	link = frappe.db.get_value("Dynamic Link", {
		"link_doctype": "Company",
		"link_name": company_name,
		"parenttype": "Address"
	}, "parent")

	if not link:
		return ""

	address = frappe.get_doc("Address", link)

	parts = []

	if address.address_line1:
		parts.append(address.address_line1)
	if address.address_line2:
		parts.append(address.address_line2)
	city_state = ", ".join(filter(None, [address.city, address.state]))
	if city_state:
		parts.append(city_state)
	if address.pincode:
		parts.append(f"P.O Box {address.pincode}")
	if address.country:
		parts.append(address.country)

	full_address = "\n".join(parts)
	return full_address
