import frappe


@frappe.whitelist()
def get_company_logo():
	"""Return company logo from Orion Settings as a base64 data URI.
	Works with S3-stored logos and bypasses permission checks."""
	import base64
	from urllib.parse import parse_qs, urlparse

	logo_url = frappe.db.get_value("Orion Settings", None, "company_logo")
	if not logo_url:
		return ""

	try:
		query = parse_qs(urlparse(logo_url).query)
		key = query.get("key", [None])[0]

		if key:
			s3_settings = frappe.get_single("S3 File Attachment")
			import boto3

			s3 = boto3.client(
				"s3",
				aws_access_key_id=s3_settings.aws_key,
				aws_secret_access_key=s3_settings.get_password("aws_secret"),
				region_name=s3_settings.region_name,
			)
			response = s3.get_object(Bucket=s3_settings.bucket_name, Key=key)
			image_bytes = response["Body"].read()
			ext = key.rsplit(".", 1)[-1].lower()
			mime_map = {
				"png": "image/png",
				"jpg": "image/jpeg",
				"jpeg": "image/jpeg",
				"gif": "image/gif",
				"svg": "image/svg+xml",
			}
			mime = mime_map.get(ext, "image/png")
			return f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
		else:
			return logo_url
	except Exception:
		return logo_url


@frappe.whitelist()
def get_customer_focal_person(party_name):
    """
    Given a Customer name, find the first Contact linked to it
    and return the formatted string for custom_customer_focal_person.
    """
    links = frappe.get_all(
        "Dynamic Link",
        filters={
            "parenttype": "Contact",
            "link_doctype": "Customer",
            "link_name": party_name
        },
        fields=["parent"],
        limit_page_length=1
    )

    if not links:
        return ""

    contact = frappe.get_doc("Contact", links[0].parent)

    lines = []
    full_name = " ".join(filter(None, [
        contact.first_name, contact.middle_name, contact.last_name
    ]))
    if full_name:
        lines.append(full_name)

    if contact.get("designation"):
        if contact.get("company_name"):
            lines.append(f"{contact.designation} - {contact.company_name}")
        else:
            lines.append(contact.designation)

    if contact.get("phone"):
        lines.append(f"Phone: {contact.phone}")
    if contact.get("mobile_no"):
        lines.append(f"Mobile: {contact.mobile_no}")
    if contact.get("email_id"):
        lines.append(f"Email: {contact.email_id}")

    return "\n".join(lines)
