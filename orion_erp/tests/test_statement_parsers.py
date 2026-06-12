# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt
"""DB-free unit tests for the portal statement parsers (no fixtures / no site data)."""

import io

import openpyxl
from frappe.tests.utils import FrappeTestCase

from orion_erp.orion_erp.doctype.fines.fines import _parse_fine_statement
from orion_erp.orion_erp.doctype.salik_or_darbs.salik_or_darbs import _parse_salik_statement

# The real 22-column header from the RTA fines portal export.
_REAL_FINE_HEADER = [
    "Fine Number", "Status", "Black Points", "Black Points Expiry Date", "Source",
    "Plate Number", "Plate Source", "Plate Color", "Plate Kind", "Ticket Type",
    "Date", "Ticket Time", "Discount Rate", "Discount Expiry Date", "Amount",
    "Late Charges", "Total Amount", "Total Amount after Discount", "Fine Location",
    "Fine Description", "Driver Traffic File Number", "Vehicle Owner Traffic File Number",
]


def _bytes(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestFineParser(FrappeTestCase):
    def test_exact_header_mapping_avoids_collisions(self):
        # A full-width row: Fine Number (col0) and Plate Number (col5) both contain "number";
        # "Fine Number" contains "fine"; "Amount" must not pick "Total Amount". Exact match wins.
        row = [None] * len(_REAL_FINE_HEADER)
        row[0] = "301260020076"          # Fine Number → ref
        row[1] = "Payable"               # Status
        row[5] = "65285"                 # Plate Number → plate
        row[10] = "2026-06-03 2:07:59"   # Date (single-digit hour)
        row[14] = " AED 500.00 "         # Amount (face value)
        row[16] = " AED 500.00 "         # Total Amount (must NOT be chosen)
        row[17] = " AED 325.00 "         # Total Amount after Discount (must NOT be chosen)
        row[18] = "Abu Dhabi-Al Nouf"    # Fine Location
        row[19] = "Exceeding speed limit"  # Fine Description

        parsed = _parse_fine_statement(_bytes([_REAL_FINE_HEADER, row]))
        self.assertEqual(len(parsed), 1)
        p = parsed[0]
        self.assertEqual(p["ref"], "301260020076")
        self.assertEqual(p["plate"], "65285")
        self.assertEqual(str(p["amount"]).strip(), " AED 500.00 ".strip())
        self.assertEqual(p["status"], "Payable")
        self.assertEqual(p["location"], "Abu Dhabi-Al Nouf")
        self.assertEqual(p["description"], "Exceeding speed limit")

    def test_rows_without_plate_are_skipped(self):
        row = [None] * len(_REAL_FINE_HEADER)
        row[0] = "F-NOPLATE"  # has a fine number but no plate
        parsed = _parse_fine_statement(_bytes([_REAL_FINE_HEADER, row]))
        self.assertEqual(parsed, [])


class TestSalikParser(FrappeTestCase):
    def test_sections_payment_skip_and_zero_skip(self):
        def txn(date, plate, gate, amount):
            r = [None] * 18
            r[1], r[5], r[7], r[10], r[13], r[17] = date, plate, "13600001", gate, "To Dubai", amount
            return r

        payment_row = [None] * 18
        payment_row[1], payment_row[15] = "2026-03-18", "600"  # date but no tag section → skipped

        rows = [
            ["Account # 1  End Balance 100"],
            ["Payment Details"],
            payment_row,
            ["Transaction Details"],
            ["Transactions for Tag # 13600001 Plate # AE Abu Dhabi Private AD 22 40269"],
            txn("2026-03-05 10:00:00 AM", "40269", "Al Garhoud", 4),
            txn("2026-03-05 10:05:00 AM", "40269", "Al Safa North", 0),  # free → skipped
            ["Total transactions for Tag # 13600001"],
            ["Transactions for Tag # 13600002 Plate # AE Abu Dhabi Public Transportation AD1  24362"],
            txn("2026-03-06 09:00:00 AM", "24362", "Jebel Ali Toll Gate", 4),
            ["Total transactions for Tag # 13600002"],
            ["Total transactions:  8.0"],
        ]
        parsed = _parse_salik_statement(_bytes(rows))
        # 2 charged crossings across 2 plates; the AED 0 row and the payment row are excluded.
        self.assertEqual(len(parsed), 2)
        self.assertEqual({p["plate"] for p in parsed}, {"40269", "24362"})
        self.assertTrue(all(p["amount"] == 4 for p in parsed))
