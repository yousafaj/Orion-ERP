# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import io

import frappe
import openpyxl
from frappe.tests.utils import FrappeTestCase
from frappe.utils.file_manager import save_file

from orion_erp.orion_erp.doctype.salik_or_darbs.salik_or_darbs import parse_and_match
from orion_erp.tests.fixtures import (
    create_customer,
    create_monthly_billing,
    create_project,
    create_vehicle,
    create_vehicle_movement,
)


def _make_xlsx(rows):
    """rows: list of (date, plate, amount). Returns xlsx bytes with a header row."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Date", "Plate", "Amount"])
    for r in rows:
        ws.append(list(r))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestSalikOrDarbs(FrappeTestCase):
    def _attach(self, batch, rows):
        content = _make_xlsx(rows)
        f = save_file("salik.xlsx", content, "Salik or Darbs", batch.name, is_private=1)
        batch.excel_attachment = f.file_url
        batch.save(ignore_permissions=True)

    def test_parse_matches_plate_and_rental(self):
        customer = create_customer()
        project = create_project(customer=customer.name)
        vehicle = create_vehicle(license_plate="DXB-55501")
        create_vehicle_movement(
            vehicle=vehicle.name,
            customer=customer.name,
            project_to=project.name,
            movement_date="2026-03-01",
        )

        batch = frappe.get_doc({"doctype": "Salik or Darbs", "date": "2026-03-31"}).insert(
            ignore_permissions=True
        )
        self._attach(
            batch,
            rows=[
                ("2026-03-10", "DXB-55501", 4),
                ("2026-03-12", "DXB-55501", 4),
                ("2026-03-15", "ZZZ-00000", 4),  # unknown plate
            ],
        )

        result = parse_and_match(batch.name)
        batch.reload()
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["unmatched"], 1)

        matched = [c for c in batch.charges if c.matched]
        self.assertEqual(len(matched), 2)
        self.assertTrue(all(c.vehicle == vehicle.name for c in matched))
        self.assertTrue(all(c.customer == customer.name for c in matched))

        unmatched = [c for c in batch.charges if not c.matched]
        self.assertEqual(unmatched[0].unmatched_reason, "Plate not found")

    def test_charge_outside_rental_is_unmatched(self):
        from orion_erp.orion_erp.doctype.vehicle_movement.vehicle_movement import demobilize

        customer = create_customer()
        project = create_project(customer=customer.name)
        vehicle = create_vehicle(license_plate="DXB-55502")
        vm = create_vehicle_movement(
            vehicle=vehicle.name,
            customer=customer.name,
            project_to=project.name,
            movement_date="2026-03-01",
        )
        demobilize(vm.name, "2026-03-20")

        batch = frappe.get_doc({"doctype": "Salik or Darbs", "date": "2026-04-30"}).insert(
            ignore_permissions=True
        )
        self._attach(batch, rows=[("2026-04-05", "DXB-55502", 4)])  # after demobilize
        parse_and_match(batch.name)
        batch.reload()
        self.assertFalse(batch.charges[0].matched)
        self.assertEqual(batch.charges[0].unmatched_reason, "No active rental on charge date")

    def test_salik_flows_into_monthly_billing(self):
        customer = create_customer()
        project = create_project(customer=customer.name)
        vehicle = create_vehicle(license_plate="DXB-55503")
        create_vehicle_movement(
            vehicle=vehicle.name,
            customer=customer.name,
            project_to=project.name,
            movement_date="2026-03-01",
        )
        batch = frappe.get_doc({"doctype": "Salik or Darbs", "date": "2026-03-31"}).insert(
            ignore_permissions=True
        )
        self._attach(batch, rows=[("2026-03-10", "DXB-55503", 4), ("2026-03-12", "DXB-55503", 6)])
        parse_and_match(batch.name)
        batch.reload()
        batch.submit()

        sheet = create_monthly_billing(customer.name, "2026-03-01", do_not_submit=True)
        self.assertEqual(len(sheet.salik_lines), 1)
        self.assertEqual(sheet.salik_lines[0].txn_count, 2)
        self.assertEqual(sheet.salik_lines[0].amount, 10)
        self.assertEqual(sheet.total_salik_amount, 10)
