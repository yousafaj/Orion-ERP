import frappe
from frappe import _

def validate_vehicle(doc, method):
    loa_to_recalc = None
    linked_cicpa_name = None
    remarks = ""
    cicpa_doc = None

    # Sync existing certificates first
    sync_existing_certificates(doc)

    if doc.custom_cicpa:
        if hasattr(doc, "custom_vehicle_certifications"):
            cicpa_exists = any(
                row.certification_name == "CICPA" and row.reference_no == doc.custom_cicpa
                for row in doc.custom_vehicle_certifications
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
        # Assign vehicle to CICPA
        frappe.db.set_value("CICPA", cicpa_doc.name, "vehicle", doc.name)
        remarks = "Adding Vehicle"

        # Add certification row only if not already present
        if hasattr(doc, "custom_vehicle_certifications"):
            already_exists = any(
                row.reference_no == cicpa_doc.name
                for row in doc.custom_vehicle_certifications
            )
            if not already_exists:
                new_row = doc.append("custom_vehicle_certifications", {})
                new_row.certification_name = "CICPA"
                new_row.date_of_issue = cicpa_doc.issue_date
                new_row.date_of_expiry = cicpa_doc.expiry_date
                new_row.attachment = cicpa_doc.document
                new_row.reference_no = cicpa_doc.name

    else:
        # Unlink vehicle from any CICPA where it's still assigned
        cicpa_docs = frappe.get_all("CICPA", filters={"vehicle": doc.name}, fields=["name", "loa"])
        for cicpa in cicpa_docs:
            frappe.db.set_value("CICPA", cicpa.name, "vehicle", None)
            frappe.db.set_value("CICPA", cicpa.name, "cicpa_status", "Cancelled")
            frappe.db.set_value("CICPA", cicpa.name, "active", "0")
            loa_to_recalc = cicpa.loa or loa_to_recalc
            linked_cicpa_name = cicpa.name
            remarks = "Removing Vehicle"

            # Remove matching certification row
            if hasattr(doc, "custom_vehicle_certifications"):
                doc.custom_vehicle_certifications = [
                    row for row in doc.custom_vehicle_certifications
                    if row.reference_no != cicpa.name
                ]

    # Recalculate LOA quotas if needed
    if loa_to_recalc:
        cicpa_list = frappe.get_all(
            "CICPA",
            filters={
                    "loa": loa_to_recalc,
                    "cicpa_type": "Vehicle"
                    },
            fields=["name", "vehicle", "cicpa_status"]
        )

        allocated_vehicle = 0
        cancelled_vehicle = 0

        for d in cicpa_list:
            if d.cicpa_status == "Cancelled":
                cancelled_vehicle += 1
            elif d.vehicle:
                allocated_vehicle += 1

        loa_doc = frappe.get_doc("LOA", loa_to_recalc)
        loa_doc.allocated_vehicle_quota = allocated_vehicle
        loa_doc.total_cancelled_vehicle_cicpa = cancelled_vehicle
        loa_doc.remaining_vehicle_quota = (
            loa_doc.total_vehicle_quota - allocated_vehicle - cancelled_vehicle
        )
        loa_doc.save(ignore_permissions=True)

    # Create CICPA Log
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
    for row in getattr(doc, "custom_vehicle_certifications", []):
        existing = frappe.get_all(
            "Existing Certificates",
            filters={
                "vehicle": doc.name,
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
                "vehicle": doc.name,
                "certificate_name": row.certification_name,
                "reference_no": row.reference_no,
                "date_of_issue": row.date_of_issue,
                "date_of_expiry": row.date_of_expiry,
                "row_name": row.name
            }).insert(ignore_permissions=True)
