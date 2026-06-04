# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import io
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_first_day, getdate

from orion_erp.orion_erp.doctype.monthly_billing.monthly_billing import rental_on_date

# Default Excel column keywords (owner can refine to real statement headers).
_DATE_KEYS = ("date", "trip date", "transaction date")
_PLATE_KEYS = ("plate", "plate no", "vehicle", "number")
_GATE_KEYS = ("gate", "toll", "location")
_AMOUNT_KEYS = ("amount", "fare", "charge", "aed", "value")
_TEMPLATE_HEADERS = ["Date", "Plate", "Gate", "Amount"]


def _norm_plate(value) -> str:
    return re.sub(r"[\s\-]", "", str(value or "")).upper()


class SalikorDarbs(Document):
    def autoname(self):
        self.billing_month = get_first_day(getdate(self.billing_month))
        self.name = f"SAL-{self.vehicle}-{self.billing_month}"

    def validate(self):
        if self.billing_month:
            self.billing_month = get_first_day(getdate(self.billing_month))
        self.total_amount = sum(flt(r.amount) for r in (self.crossings or []))


# ---------------------------------------------------------------------------
# Bulk import — one monthly Excel → one Salik doc per vehicle
# ---------------------------------------------------------------------------
@frappe.whitelist()
def import_salik(file_url, billing_month):
    frappe.has_permission("Salik or Darbs", "create", throw=True)
    month = get_first_day(getdate(billing_month))
    rows = _read_workbook(file_url)
    if not rows:
        frappe.throw(_("No data rows found in the attached Excel."))

    plate_index = _build_plate_index()
    by_vehicle, unmatched = {}, 0
    for r in rows:
        vehicle = plate_index.get(_norm_plate(r.get("plate")))
        if vehicle:
            by_vehicle.setdefault(vehicle, []).append(r)
        else:
            unmatched += 1

    for vehicle, crossings in by_vehicle.items():
        doc = _get_or_create(vehicle, month)
        for r in crossings:
            charge_date = getdate(r["date"]) if r.get("date") else month
            rental = rental_on_date(vehicle, charge_date)
            doc.append(
                "crossings",
                {
                    "charge_date": charge_date,
                    "gate": r.get("gate"),
                    "amount": flt(r.get("amount")),
                    "vehicle": vehicle,
                    "customer": rental.customer if rental else None,
                    "rental": rental.name if rental else None,
                    "company_cost": 0 if rental else 1,
                },
            )
        doc.save(ignore_permissions=True)

    return {"vehicles": len(by_vehicle), "unmatched": unmatched}


def _get_or_create(vehicle, month):
    name = frappe.db.exists("Salik or Darbs", {"vehicle": vehicle, "billing_month": month, "docstatus": ["<", 2]})
    if name:
        return frappe.get_doc("Salik or Darbs", name)
    return frappe.get_doc({"doctype": "Salik or Darbs", "vehicle": vehicle, "billing_month": month})


@frappe.whitelist()
def download_template():
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Salik"
    ws.append(_TEMPLATE_HEADERS)
    buf = io.BytesIO()
    wb.save(buf)
    frappe.response["filename"] = "salik_template.xlsx"
    frappe.response["filecontent"] = buf.getvalue()
    frappe.response["type"] = "download"


# ---------------------------------------------------------------------------
# Excel reading helpers
# ---------------------------------------------------------------------------
def _read_workbook(file_url):
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
                "gate": _cell(raw, col.get("gate")),
                "amount": _cell(raw, col.get("amount")),
            }
        )
    return out


def _detect_columns(header):
    def find(keys):
        for i, h in enumerate(header):
            if h in keys:
                return i
        for i, h in enumerate(header):
            if any(k in h for k in keys):
                return i
        return None

    return {
        "date": find(_DATE_KEYS),
        "plate": find(_PLATE_KEYS),
        "gate": find(_GATE_KEYS),
        "amount": find(_AMOUNT_KEYS),
    }


def _cell(row, idx):
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _build_plate_index():
    index = {}
    for v in frappe.get_all("Vehicle", fields=["name", "license_plate", "custom_plate_code"]):
        plate = v.license_plate or v.name
        index[_norm_plate(plate)] = v.name
        if v.custom_plate_code:
            index[_norm_plate(f"{v.custom_plate_code}{plate}")] = v.name
    return index
