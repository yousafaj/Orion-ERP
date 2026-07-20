# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from orion_erp.orion_erp.services.cicpa import (
    validate_cicpa_quota,
    update_loa_on_submit,
    update_loa_on_trash,
    update_loa_on_cancel,
    update_vehicle_certification,
    update_driver_certification,
    cleanup_cicpa_logs,
    remove_vehicle_certification,
    remove_driver_certification,
    mark_cicpa_status,
    auto_expire_cicpas,
)


class CICPA(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        active: DF.Check
        amended_from: DF.Link | None
        cicpa_no: DF.Data | None
        cicpa_status: DF.Literal["", "Active", "Cancelled", "Lost", "Expired"]
        cicpa_type: DF.Literal["", "Driver", "Vehicle"]
        company: DF.Link | None
        document: DF.Attach | None
        driver: DF.Link | None
        expiry_date: DF.Date
        issue_date: DF.Date
        loa: DF.Link
        vehicle: DF.Link | None
    # end: auto-generated types

    def validate(self):
        if not self.loa or not self.cicpa_type:
            return
        loa_doc = frappe.get_doc("LOA", self.loa)
        validate_cicpa_quota(self.cicpa_type, loa_doc)

    def on_submit(self):
        if not self.loa:
            return
        try:
            loa_doc = frappe.get_doc("LOA", self.loa)
            update_loa_on_submit(self.cicpa_type, loa_doc)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error updating LOA CICPA count on submit")
            frappe.throw(_("Failed to update LOA record: {0}").format(str(e)))

    def on_trash(self):
        if not self.loa or self.docstatus != 1 or self.cicpa_status != "Active":
            return
        try:
            loa_doc = frappe.get_doc("LOA", self.loa)
            update_loa_on_trash(self.cicpa_type, loa_doc)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error updating LOA CICPA count on delete")
            frappe.throw(_("Failed to update LOA record during deletion: {0}").format(str(e)))

    def on_change(self):
        update_vehicle_certification(self)
        update_driver_certification(self)

    def before_cancel(self):
        if self.cicpa_status == "Active" and self.loa:
            try:
                loa = frappe.get_doc("LOA", self.loa)
                update_loa_on_cancel(self.cicpa_type, loa)
            except Exception:
                frappe.log_error(frappe.get_traceback(), "CICPA before_cancel: LOA quota update failed")
            self.db_set("cicpa_status", "Cancelled", update_modified=True)

        if self.loa:
            self.db_set("loa", None, update_modified=False)

        try:
            cleanup_cicpa_logs(self.name)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "CICPA before_cancel: CICPA Logs cleanup failed")
            frappe.throw(_("Cannot cancel CICPA due to linked CICPA Logs: {0}").format(str(e)))

        remove_vehicle_certification(self)
        remove_driver_certification(self)
