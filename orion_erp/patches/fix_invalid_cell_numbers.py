import frappe

def execute():
    # Clean invalid phone values (0, 0.0) after changing fields from Data to Phone
    frappe.db.sql("""
        UPDATE `tabEmployee`
        SET 
            cell_number = NULL,
            custom_company_mobile_no = NULL,
            emergency_phone_number = NULL
        WHERE 
            cell_number IN ('0','0.0')
            OR custom_company_mobile_no IN ('0','0.0')
            OR emergency_phone_number IN ('0','0.0')
    """)