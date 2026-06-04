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


def _xlsx(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Date", "Plate", "Gate", "Amount"])
    for r in rows:
        ws.append(list(r))
    buf = io.BytesIO()
    wb.save(buf)
    return save_file("salik.xlsx", buf.getvalue(), None, None, is_private=1).file_url


class TestSalik(FrappeTestCase):
    def test_import_creates_per_vehicle_doc_and_matches_customer(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle(license_plate="DXB-71001")
        create_vehicle_movement(vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01")

        f = _xlsx([("2026-03-05", "DXB-71001", "Al Garhoud", 4), ("2026-03-09", "DXB-71001", "Al Maktoum", 4)])
        result = import_salik(f, "2026-03-01")
        self.assertEqual(result["vehicles"], 1)

        name = frappe.db.get_value("Salik or Darbs", {"vehicle": vehicle.name, "billing_month": "2026-03-01"})
        doc = frappe.get_doc("Salik or Darbs", name)
        self.assertEqual(len(doc.crossings), 2)
        self.assertEqual(doc.total_amount, 8)
        self.assertTrue(all(c.customer == customer and not c.company_cost for c in doc.crossings))

    def test_toll_without_rental_is_company_cost(self):
        vehicle = create_vehicle(license_plate="DXB-71002")
        f = _xlsx([("2026-03-05", "DXB-71002", "Gate", 4)])
        import_salik(f, "2026-03-01")
        name = frappe.db.get_value("Salik or Darbs", {"vehicle": vehicle.name, "billing_month": "2026-03-01"})
        doc = frappe.get_doc("Salik or Darbs", name)
        self.assertTrue(doc.crossings[0].company_cost)

    def test_salik_flows_into_monthly_billing(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle(license_plate="DXB-71003")
        create_vehicle_movement(vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01")
        f = _xlsx([("2026-03-05", "DXB-71003", "G", 4), ("2026-03-06", "DXB-71003", "G", 6)])
        import_salik(f, "2026-03-01")
        frappe.get_doc("Salik or Darbs", frappe.db.get_value("Salik or Darbs", {"vehicle": vehicle.name})).submit()

        sheet = create_monthly_billing(customer, "2026-03-01", do_not_submit=True)
        self.assertEqual(len(sheet.salik_lines), 1)
        self.assertEqual(sheet.salik_lines[0].amount, 10)
        self.assertEqual(sheet.total_salik_amount, 10)
