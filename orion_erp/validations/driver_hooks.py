import frappe
from frappe import _

def validate_driver(doc, method):
    loa_to_recalc = None
    linked_cicpa_name = None
    remarks = ""
    cicpa_doc = None
    sync_existing_certificates(doc)
    if doc.custom_cicpa:
        if hasattr(doc, "custom_certification_list"):
            cicpa_exists = any(
                row.certification_name == "CICPA" and row.reference_no == doc.custom_cicpa
                for row in doc.custom_certification_list
            )
            if cicpa_exists:
                return

        try:
            cicpa_doc = frappe.get_doc("CICPA", doc.custom_cicpa)
            loa_to_recalc = cicpa_doc.loa
            linked_cicpa_name = cicpa_doc.name
        except frappe.DoesNotExistError:
            pass

    if doc.custom_has_cicpa and cicpa_doc:
        frappe.db.set_value("CICPA", cicpa_doc.name, "driver", doc.name)
        remarks = "Adding Driver"

        if hasattr(doc, "custom_certification_list"):
            already_exists = any(
                row.reference_no == cicpa_doc.name
                for row in doc.custom_certification_list
            )
            if not already_exists:
                new_row = doc.append("custom_certification_list", {})
                new_row.certification_name = "CICPA"
                new_row.date_of_issue = cicpa_doc.issue_date
                new_row.date_of_expiry = cicpa_doc.expiry_date
                new_row.attachment = cicpa_doc.document
                new_row.reference_no = cicpa_doc.name

    else:
        cicpa_docs = frappe.get_all("CICPA", filters={"driver": doc.name}, fields=["name", "loa"])
        for cicpa in cicpa_docs:
            frappe.db.set_value("CICPA", cicpa.name, "driver", None)
            frappe.db.set_value("CICPA", cicpa.name, "cicpa_status", "Cancelled")
            frappe.db.set_value("CICPA", cicpa.name, "active", "0")
            loa_to_recalc = cicpa.loa or loa_to_recalc
            linked_cicpa_name = cicpa.name
            remarks = "Removing Driver"

            if hasattr(doc, "custom_certification_list"):
                doc.custom_certification_list = [
                    row for row in doc.custom_certification_list
                    if row.reference_no != cicpa.name
                ]

    if loa_to_recalc:
        cicpa_list = frappe.get_all(
            "CICPA",
            filters={
                "loa": loa_to_recalc,
                "cicpa_type": "Driver"
            },
            fields=["name", "driver", "cicpa_status"]
        )

        allocated_driver = 0
        cancelled_driver = 0

        for d in cicpa_list:
            if d.cicpa_status == "Cancelled":
                cancelled_driver += 1
            elif d.driver:
                allocated_driver += 1

        loa_doc = frappe.get_doc("LOA", loa_to_recalc)
        loa_doc.allocated_driver_quota = allocated_driver
        loa_doc.total_cancelled_driver_cicpa = cancelled_driver
        loa_doc.remaining_driver_quota = (
            loa_doc.total_driver_quota - allocated_driver - cancelled_driver
        )

        loa_doc.save(ignore_permissions=True)

    if linked_cicpa_name and remarks:
        cicpa_record = frappe.get_doc("CICPA", linked_cicpa_name)
        frappe.get_doc({
            "doctype": "CICPA Logs",
            "cicpa": cicpa_record.name,
            "loa": cicpa_record.loa,
            "vehicle": cicpa_record.vehicle,
            "driver": cicpa_record.driver,
            "remarks": remarks,
            "docstatus": 1
        }).insert(ignore_permissions=True)

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
