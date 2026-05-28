import frappe

@frappe.whitelist()
def fetch_customer_locations_query(doctype, txt, searchfield, start, page_len, filters):
    customer_name = filters.get('customer_name')

    return frappe.db.sql("""
        SELECT location, location
        FROM `tabCustomer Locations cdt`
        WHERE parent = %s AND location LIKE %s
        LIMIT %s, %s
    """, (customer_name, f"%{txt}%", start, page_len))
