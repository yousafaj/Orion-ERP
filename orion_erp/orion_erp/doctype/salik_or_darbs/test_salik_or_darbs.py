# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import io

import frappe
import openpyxl
from frappe.tests.utils import FrappeTestCase
from frappe.utils.file_manager import save_file

from orion_erp.orion_erp.doctype.salik_or_darbs.salik_or_darbs import import_salik
from orion_erp.tests.fixtures import (
    create_customer,
    create_monthly_billing,
    create_project,
    create_vehicle,
    create_vehicle_movement,
)


def _portal_salik_xlsx(sections):
    """Build a workbook mirroring the portal's sectioned Salik statement.

    `sections` is a list of (plate, crossings); each crossing is
    (date, gate, direction, amount). Transaction values sit at the portal's
    fixed columns date=1, plate=5, tag=7, gate=10, direction=13, amount=17.
    Account/Summary/Payment junk before the first tag header must be ignored.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Table 1"
    ws.append(["Account # 35627901  Name Orion  End Balance(AED) 1,714.00"])
    ws.append(["Summary"])
    ws.append(["Payment Details"])
    pay = [None] * 18
    pay[1], pay[15] = "2026-03-18 00:00:00", "600"  # payment row: date but no tag section → skipped
    ws.append(pay)
    ws.append(["Transaction Details"])

    tag = 13600000
    for plate, crossings in sections:
        tag += 1
        ws.append([f"Transactions for Tag # {tag} Plate # AE Abu Dhabi Private AD 22 {plate}"])
        for date, gate, direction, amount in crossings:
            row = [None] * 18
            row[1], row[5], row[7], row[10], row[13], row[17] = date, str(plate), str(tag), gate, direction, amount
            ws.append(row)
        ws.append([f"Total transactions for Tag # {tag}"])
    ws.append(["Total transactions:   624.0"])
    buf = io.BytesIO()
    wb.save(buf)
    return save_file("salik.xlsx", buf.getvalue(), None, None, is_private=1).file_url


class TestSalik(FrappeTestCase):
    def test_import_creates_per_vehicle_doc_and_matches_customer(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle(license_plate="71001")
        create_vehicle_movement(vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01")

        f = _portal_salik_xlsx(
            [
                (
                    "71001",
                    [
                        ("2026-03-05 10:00:00 AM", "Al Garhoud", "To Dubai", 4),
                        ("2026-03-09 11:00:00 AM", "Al Maktoum", "To Sharjah", 4),
                        ("2026-03-09 11:05:00 AM", "Al Safa North", "To Sharjah", 0),  # free → skipped
                    ],
                )
            ]
        )
        result = import_salik(f, "2026-03-01")
        self.assertEqual(result["vehicles"], 1)

        name = frappe.db.get_value("Salik or Darbs", {"vehicle": vehicle.name, "billing_month": "2026-03-01"})
        doc = frappe.get_doc("Salik or Darbs", name)
        self.assertEqual(len(doc.crossings), 2)  # AED 0 crossing skipped
        self.assertEqual(doc.total_amount, 8)
        self.assertTrue(all(c.customer == customer and not c.company_cost for c in doc.crossings))

    def test_toll_without_rental_is_company_cost(self):
        vehicle = create_vehicle(license_plate="71002")
        f = _portal_salik_xlsx([("71002", [("2026-03-05 09:00:00 AM", "Gate", "To Dubai", 4)])])
        import_salik(f, "2026-03-01")
        name = frappe.db.get_value("Salik or Darbs", {"vehicle": vehicle.name, "billing_month": "2026-03-01"})
        doc = frappe.get_doc("Salik or Darbs", name)
        self.assertTrue(doc.crossings[0].company_cost)

    def test_zero_skipped_and_parking_included(self):
        vehicle = create_vehicle(license_plate="71009")
        f = _portal_salik_xlsx(
            [
                (
                    "71009",
                    [
                        ("2026-03-05 10:00:00 AM", "Jebel Ali Toll Gate", "To Abu Dhabi", 4),
                        ("2026-03-05 12:00:00 PM", "Mawaqif Parking Zone A", "", 10),  # parking → included
                        ("2026-03-05 12:30:00 PM", "Al Safa North", "To Sharjah", 0),  # free → skipped
                    ],
                )
            ]
        )
        import_salik(f, "2026-03-01")
        doc = frappe.get_doc("Salik or Darbs", frappe.db.get_value("Salik or Darbs", {"vehicle": vehicle.name}))
        self.assertEqual(len(doc.crossings), 2)
        self.assertEqual(doc.total_amount, 14)

    def test_reimport_is_idempotent(self):
        vehicle = create_vehicle(license_plate="71010")
        rows = [("71010", [("2026-03-05 10:00:00 AM", "Al Garhoud", "To Dubai", 4)])]
        import_salik(_portal_salik_xlsx(rows), "2026-03-01")
        import_salik(_portal_salik_xlsx(rows), "2026-03-01")  # re-import same statement
        doc = frappe.get_doc("Salik or Darbs", frappe.db.get_value("Salik or Darbs", {"vehicle": vehicle.name}))
        self.assertEqual(len(doc.crossings), 1)  # not double-appended

    def test_salik_flows_into_monthly_billing(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle(license_plate="71003")
        create_vehicle_movement(vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01")
        f = _portal_salik_xlsx(
            [
                (
                    "71003",
                    [
                        ("2026-03-05 10:00:00 AM", "G", "To Dubai", 4),
                        ("2026-03-06 10:00:00 AM", "G", "To Dubai", 6),
                    ],
                )
            ]
        )
        import_salik(f, "2026-03-01")
        frappe.get_doc("Salik or Darbs", frappe.db.get_value("Salik or Darbs", {"vehicle": vehicle.name})).submit()

        sheet = create_monthly_billing(customer, "2026-03-01", do_not_submit=True)
        self.assertEqual(len(sheet.salik_lines), 1)
        self.assertEqual(sheet.salik_lines[0].amount, 10)
        self.assertEqual(sheet.total_salik_amount, 10)
