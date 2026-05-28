import frappe


def validate_driver(doc, method):
    pull_certificates_from_employee(doc)
    ensure_driver_certification_types(doc)
    if not doc.is_new():
        sync_existing_certificates(doc)


def after_insert_driver(doc, method):
    sync_existing_certificates(doc)


def pull_certificates_from_employee(doc):
    if not doc.is_new() or not doc.employee or doc.get("custom_certification_list"):
        return

    emp_rows = frappe.get_all(
        "Employee cdt",
        filters={"parent": doc.employee, "parentfield": "custom_certificates"},
        fields=["certification_name", "reference_no", "date_of_issue", "date_of_expiry", "attachment"],
        order_by="idx asc",
    )
    for row in emp_rows:
        doc.append("custom_certification_list", row)


def ensure_driver_certification_types(doc):
    for row in doc.get("custom_certification_list", []) or []:
        cert_name = getattr(row, "certification_name", None)
        _ensure_cert_type(cert_name)


def _ensure_cert_type(cert_name):
    if cert_name and not frappe.db.exists("Driver Certification Type", cert_name):
        frappe.get_doc({
            "doctype": "Driver Certification Type",
            "type_name": cert_name,
        }).insert(ignore_permissions=True)


@frappe.whitelist()
def get_employee_certificates_for_driver(employee):
    if not employee:
        return []

    rows = frappe.get_all(
        "Employee cdt",
        filters={"parent": employee, "parentfield": "custom_certificates"},
        fields=["certification_name", "reference_no", "date_of_issue", "date_of_expiry", "attachment"],
        order_by="idx asc",
    )
    for r in rows:
        _ensure_cert_type(r.get("certification_name"))
    return rows


def sync_existing_certificates(doc):
    for row in getattr(doc, "custom_certification_list", []):
        existing = frappe.get_all(
            "Existing Certificates",
            filters={
                "driver": doc.name,
                "certificate_name": row.certification_name,
                "reference_no": row.reference_no
            },
            fields=["name", "date_of_expiry"]
        )

        if existing:
            existing_cert = existing[0]
            if str(existing_cert.date_of_expiry) != str(row.date_of_expiry):
                frappe.db.set_value("Existing Certificates", existing_cert.name, "date_of_expiry", row.date_of_expiry)
        else:
            frappe.get_doc({
                "doctype": "Existing Certificates",
                "driver": doc.name,
                "certificate_name": row.certification_name,
                "reference_no": row.reference_no,
                "date_of_issue": row.date_of_issue,
                "date_of_expiry": row.date_of_expiry,
                "row_name": row.name
            }).insert(ignore_permissions=True)
