# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import io
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from orion_erp.orion_erp.doctype.monthly_billing.monthly_billing import rental_on_date


# Header keywords used to locate columns in the toll-authority Excel.
_DATE_KEYS = ("date", "trip date", "transaction date", "txn date")
_PLATE_KEYS = ("plate", "plate no", "plate number", "vehicle", "number")
_AMOUNT_KEYS = ("amount", "toll", "charge", "fare", "value", "aed")


def _norm_plate(value) -> str:
    """Normalize a plate for matching: drop spaces/dashes, uppercase."""
    return re.sub(r"[\s\-]", "", str(value or "")).upper()


class SalikorDarbs(Document):
    def parse_and_match(self):
        """Parse the attached Excel into Salik Charge rows and auto-match each
        toll to a vehicle and the rental active on the charge date."""
        if not self.excel_attachment:
            frappe.throw(_("Attach the toll statement Excel first."))

        rows = _read_workbook(self.excel_attachment)
        if not rows:
            frappe.throw(_("No data rows found in the attached Excel."))

        plate_index = _build_plate_index()

        self.set("charges", [])
        unmatched = 0
        for r in rows:
            charge = {
                "charge_date": getdate(r["date"]) if r.get("date") else None,
                "plate": r.get("plate"),
                "amount": flt(r.get("amount")),
                "matched": 0,
            }
            vehicle = plate_index.get(_norm_plate(r.get("plate")))
            if not vehicle:
                charge["unmatched_reason"] = "Plate not found"
                unmatched += 1
            elif not r.get("date"):
                charge["vehicle"] = vehicle
                charge["unmatched_reason"] = "Missing charge date"
                unmatched += 1
            else:
                charge["vehicle"] = vehicle
                rental = rental_on_date(vehicle, r["date"])
                if not rental:
                    charge["unmatched_reason"] = "No active rental on charge date"
                    unmatched += 1
                else:
                    charge["rental"] = rental.name
                    charge["customer"] = rental.customer
                    charge["project"] = rental.project_to
                    charge["matched"] = 1
            self.append("charges", charge)

        self.unmatched_count = unmatched


def _read_workbook(file_url):
    """Return a list of {date, plate, amount} dicts from the attached workbook.
    Resolves the file via the File API so S3-backed attachments work."""
    import openpyxl

    file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
    if not file_name:
        frappe.throw(_("Could not resolve the attached file."))
    content = frappe.get_doc("File", file_name).get_content()
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    header = [str(c).strip().lower() if c is not None else "" for c in rows[0]]
    col = _detect_columns(header)
    out = []
    for raw in rows[1:]:
        if raw is None or all(c is None for c in raw):
            continue
        out.append(
            {
                "date": _cell(raw, col.get("date")),
                "plate": _cell(raw, col.get("plate")),
                "amount": _cell(raw, col.get("amount")),
            }
        )
    return out


def _detect_columns(header):
    def find(keys):
        # exact header match first, then substring match
        for i, h in enumerate(header):
            if h in keys:
                return i
        for i, h in enumerate(header):
            if any(k in h for k in keys):
                return i
        return None

    return {"date": find(_DATE_KEYS), "plate": find(_PLATE_KEYS), "amount": find(_AMOUNT_KEYS)}


def _cell(row, idx):
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _build_plate_index():
    """Map several normalized plate representations to a vehicle name."""
    index = {}
    for v in frappe.get_all("Vehicle", fields=["name", "license_plate", "custom_plate_code"]):
        plate = v.license_plate or v.name
        index[_norm_plate(plate)] = v.name
        if v.custom_plate_code:
            index[_norm_plate(f"{v.custom_plate_code}{plate}")] = v.name
    return index


@frappe.whitelist()
def parse_and_match(name):
    """Operations action: parse the attached Excel + auto-match, then save."""
    doc = frappe.get_doc("Salik or Darbs", name)
    if doc.docstatus != 0:
        frappe.throw(_("Parse the statement while the batch is still a draft."))
    doc.parse_and_match()
    doc.save(ignore_permissions=True)
    return {"total": len(doc.charges), "unmatched": doc.unmatched_count}
