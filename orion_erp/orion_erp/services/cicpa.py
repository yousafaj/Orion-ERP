import frappe
from frappe import _


def _notify_loa(loa_name):
    if loa_name:
        frappe.publish_realtime(
            "orion_loa_quota_updated", {"loa": loa_name}, doctype="LOA", docname=loa_name
        )


def validate_cicpa_quota(cicpa_type, loa_doc):
    if cicpa_type == "Vehicle":
        if loa_doc.remaining_vehicle_quota <= 0 or loa_doc.total_created_vehicle_cicpa >= loa_doc.total_vehicle_quota:
            frappe.throw(_("Cannot create CICPA: Vehicle quota exhausted or invalid in LOA {0}.").format(loa_doc.name))
    elif cicpa_type == "Driver":
        if loa_doc.remaining_driver_quota <= 0 or loa_doc.total_created_driver_cicpa >= loa_doc.total_driver_quota:
            frappe.throw(_("Cannot create CICPA: Driver quota exhausted or invalid in LOA {0}.").format(loa_doc.name))


def update_loa_on_submit(cicpa_type, loa_doc):
    if cicpa_type == "Vehicle":
        loa_doc.total_created_vehicle_cicpa = (loa_doc.total_created_vehicle_cicpa or 0) + 1
        loa_doc.remaining_vehicle_quota = max(0, (loa_doc.remaining_vehicle_quota or 0) - 1)
    elif cicpa_type == "Driver":
        loa_doc.total_created_driver_cicpa = (loa_doc.total_created_driver_cicpa or 0) + 1
        loa_doc.remaining_driver_quota = max(0, (loa_doc.remaining_driver_quota or 0) - 1)

    loa_doc.save(ignore_permissions=True)
    _notify_loa(loa_doc.name)


def update_loa_on_trash(cicpa_type, loa_doc):
    if cicpa_type == "Vehicle":
        loa_doc.total_created_vehicle_cicpa = max(0, (loa_doc.total_created_vehicle_cicpa or 0) - 1)
        loa_doc.remaining_vehicle_quota = (loa_doc.remaining_vehicle_quota or 0) + 1
    elif cicpa_type == "Driver":
        loa_doc.total_created_driver_cicpa = max(0, (loa_doc.total_created_driver_cicpa or 0) - 1)
        loa_doc.remaining_driver_quota = (loa_doc.remaining_driver_quota or 0) + 1

    loa_doc.save(ignore_permissions=True)
    _notify_loa(loa_doc.name)


def update_loa_on_cancel(cicpa_type, loa):
    if cicpa_type == "Vehicle":
        loa.total_created_vehicle_cicpa = max(0, (loa.total_created_vehicle_cicpa or 0) - 1)
        loa.remaining_vehicle_quota = (loa.remaining_vehicle_quota or 0) + 1
        loa.total_cancelled_vehicle_cicpa = (loa.total_cancelled_vehicle_cicpa or 0) + 1
    elif cicpa_type == "Driver":
        loa.total_created_driver_cicpa = max(0, (loa.total_created_driver_cicpa or 0) - 1)
        loa.remaining_driver_quota = (loa.remaining_driver_quota or 0) + 1
        loa.total_cancelled_driver_cicpa = (loa.total_cancelled_driver_cicpa or 0) + 1

    loa.save(ignore_permissions=True)
    _notify_loa(loa.name)


def update_vehicle_certification(cicpa):
    if cicpa.cicpa_type != "Vehicle" or not cicpa.vehicle:
        return

    try:
        vehicle_doc = frappe.get_doc("Vehicle", cicpa.vehicle)
        updated = False
        for row in vehicle_doc.get("custom_vehicle_certifications", []):
            if row.certification_name == "CICPA" and row.reference_no == cicpa.name:
                row.date_of_expiry = cicpa.expiry_date
                updated = True
                break
        if updated:
            vehicle_doc.flags.ignore_mandatory = True
            vehicle_doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error updating CICPA expiry date in Vehicle")
        frappe.throw(_("Failed to update CICPA expiry date in Vehicle: {0}").format(str(e)))


def update_driver_certification(cicpa):
    if cicpa.cicpa_type != "Driver" or not cicpa.driver:
        return

    try:
        driver_doc = frappe.get_doc("Driver", cicpa.driver)
        updated = False
        for row in driver_doc.get("custom_certification_list", []):
            if row.certification_name == "CICPA" and row.reference_no == cicpa.name:
                row.date_of_expiry = cicpa.expiry_date
                updated = True
                break
        if updated:
            driver_doc.flags.ignore_mandatory = True
            driver_doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error updating CICPA expiry date in Driver")
        frappe.throw(_("Failed to update CICPA expiry date in Driver: {0}").format(str(e)))


def cleanup_cicpa_logs(cicpa_name):
    cicpa_logs = frappe.get_all(
        "CICPA Logs", filters={"cicpa": cicpa_name}, fields=["name", "docstatus"]
    )
    for log in cicpa_logs:
        frappe.db.set_value("CICPA Logs", log.name, "cicpa", None)
        log_doc = frappe.get_doc("CICPA Logs", log.name)
        if log_doc.docstatus == 1:
            log_doc.cancel()
        log_doc.delete(ignore_permissions=True)


def remove_vehicle_certification(cicpa):
    if cicpa.cicpa_type != "Vehicle" or not cicpa.vehicle:
        return

    try:
        vehicle_doc = frappe.get_doc("Vehicle", cicpa.vehicle)
        vehicle_doc.custom_vehicle_certifications = [
            row for row in vehicle_doc.get("custom_vehicle_certifications", [])
            if not (row.certification_name == "CICPA" and row.reference_no == cicpa.name)
        ]
        vehicle_doc.flags.ignore_mandatory = True
        vehicle_doc.save(ignore_permissions=True)
        if cicpa.vehicle:
            cicpa.db_set("vehicle", None, update_modified=False)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "CICPA before_cancel: Vehicle cleanup failed")
        frappe.throw(_("Failed to clean CICPA from Vehicle: {0}").format(str(e)))


def remove_driver_certification(cicpa):
    if cicpa.cicpa_type != "Driver" or not cicpa.driver:
        return

    try:
        driver_doc = frappe.get_doc("Driver", cicpa.driver)
        driver_doc.custom_certification_list = [
            row for row in driver_doc.get("custom_certification_list", [])
            if not (row.certification_name == "CICPA" and row.reference_no == cicpa.name)
        ]
        driver_doc.flags.ignore_mandatory = True
        driver_doc.save(ignore_permissions=True)
        if cicpa.driver:
            cicpa.db_set("driver", None, update_modified=False)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "CICPA before_cancel: Driver cleanup failed")
        frappe.throw(_("Failed to clean CICPA from Driver: {0}").format(str(e)))


@frappe.whitelist()
def mark_cicpa_status(cicpa, new_status):
    if new_status not in ("Cancelled", "Expired"):
        frappe.throw(_("Invalid CICPA status."))

    doc = frappe.get_doc("CICPA", cicpa)
    if doc.docstatus != 1:
        frappe.throw(_("CICPA must be submitted before status can be changed."))
    if doc.cicpa_status != "Active":
        frappe.throw(_("CICPA status is already {0}.").format(doc.cicpa_status))

    doc.db_set("cicpa_status", new_status, update_modified=True)

    if doc.loa:
        _update_loa_counters(doc.loa, doc.cicpa_type, new_status)


def _update_loa_counters(loa_name, cicpa_type, new_status):
    loa = frappe.get_doc("LOA", loa_name)
    if cicpa_type == "Vehicle":
        loa.total_created_vehicle_cicpa = max(0, (loa.total_created_vehicle_cicpa or 0) - 1)
        loa.remaining_vehicle_quota = (loa.remaining_vehicle_quota or 0) + 1
        if new_status == "Cancelled":
            loa.total_cancelled_vehicle_cicpa = (loa.total_cancelled_vehicle_cicpa or 0) + 1
    elif cicpa_type == "Driver":
        loa.total_created_driver_cicpa = max(0, (loa.total_created_driver_cicpa or 0) - 1)
        loa.remaining_driver_quota = (loa.remaining_driver_quota or 0) + 1
        if new_status == "Cancelled":
            loa.total_cancelled_driver_cicpa = (loa.total_cancelled_driver_cicpa or 0) + 1

    loa.save(ignore_permissions=True)
    _notify_loa(loa.name)


def auto_expire_cicpas():
    today = frappe.utils.nowdate()
    candidates = frappe.get_all(
        "CICPA",
        filters={"docstatus": 1, "cicpa_status": "Active", "expiry_date": ["<", today]},
        pluck="name",
    )
    for name in candidates:
        try:
            mark_cicpa_status(name, "Expired")
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), f"auto_expire_cicpas failed for {name}")
