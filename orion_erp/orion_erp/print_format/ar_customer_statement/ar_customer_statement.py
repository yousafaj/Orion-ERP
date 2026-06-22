
import frappe
import base64
import boto3

@frappe.whitelist()
def get_enrichment_data(company=None, customer=None):
    result = {}

    # Company Details
    if company:
        company_doc = frappe.get_doc("Company", company)

        company_address_name = frappe.db.sql(
            """
            SELECT a.name
            FROM `tabAddress` a
            INNER JOIN `tabDynamic Link` dl
                ON dl.parent = a.name
            WHERE dl.link_doctype = 'Company'
                AND dl.link_name = %s
                AND a.is_primary_address = 1
            LIMIT 1
            """,
            company,
            as_dict=True,
        )

        company_address = {}
        if company_address_name:
            company_address = frappe.get_doc(
                "Address", company_address_name[0].name
            ).as_dict()
        
        result.update({
            "company_name": company_doc.company_name or "",
            "company_address_line1": company_address.get("address_line1", ""),
            "company_address_line2": company_address.get("address_line2", ""),
            "company_city": company_address.get("city", ""),
            "company_state": company_address.get("state", ""),
            "company_country": company_address.get("country", ""),
            "company_pincode": company_address.get("pincode", ""),
            "company_phone": company_address.get("phone", "") or company_doc.phone_no or "",
            "company_email": company_address.get("email_id", "") or company_doc.email or "",
            "company_fax": company_address.get("fax", "") or company_doc.fax or "",
            "company_trn": company_doc.tax_id or "",
        })

        
        from urllib.parse import parse_qs, urlparse

        logo_url = frappe.db.get_single_value("Orion Settings", "company_logo")

        if logo_url:
            # Extract key from URL
            query = parse_qs(urlparse(logo_url).query)
            key = query.get("key", [None])[0]

            if key:
                s3_settings = frappe.get_single("S3 File Attachment")

                s3 = boto3.client(
                    "s3",
                    aws_access_key_id=s3_settings.aws_key,
                    aws_secret_access_key=s3_settings.get_password("aws_secret"),
                    region_name=s3_settings.region_name
                )

                response = s3.get_object(
                    Bucket=s3_settings.bucket_name,
                    Key=key
                )

                image_bytes = response["Body"].read()

                result["company_logo"] = (
                    "data:image/png;base64,"
                    + base64.b64encode(image_bytes).decode()
                )
    # Customer Details
    if customer:
        customer_doc = frappe.get_doc("Customer", customer)

        customer_address_name = frappe.db.sql(
            """
            SELECT a.name
            FROM `tabAddress` a
            INNER JOIN `tabDynamic Link` dl
                ON dl.parent = a.name
            WHERE dl.link_doctype = 'Customer'
                AND dl.link_name = %s
                AND a.is_primary_address = 1
            LIMIT 1
            """,
            customer,
            as_dict=True,
        )

        customer_address = {}
        if customer_address_name:
            customer_address = frappe.get_doc(
                "Address", customer_address_name[0].name
            ).as_dict()

        result.update({
            "customer_name": customer_doc.customer_name or "",
            "customer_address_line1": customer_address.get("address_line1", ""),
            "customer_address_line2": customer_address.get("address_line2", ""),
            "customer_city": customer_address.get("city", ""),
            "customer_state": customer_address.get("state", ""),
            "customer_country": customer_address.get("country", ""),
            "customer_pincode": customer_address.get("pincode", ""),
            "customer_phone": customer_address.get("phone", ""),
            "customer_email": customer_address.get("email_id", ""),
            "customer_trn": customer_doc.tax_id or "",
        })

    return result