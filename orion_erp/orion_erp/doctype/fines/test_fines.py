# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import io

import frappe
import openpyxl
from frappe.tests.utils import FrappeTestCase
from frappe.utils.file_manager import save_file

from orion_erp.orion_erp.doctype.traffic_fine_or_accident.traffic_fine_or_accident import (
    create_employee_deduction,
    import_fines,
)
from orion_erp.tests.fixtures import (
    create_customer,
    create_driver,
    create_monthly_billing,
    create_project,
    create_vehicle,
    create_vehicle_movement,
)


def create_fine(do_not_submit=False, **kwargs):
    values = {
        "doctype": "Traffic Fine or Accident",
        "vehicle": kwargs.pop("vehicle", None) or create_vehicle().name,
        "date": kwargs.pop("date", "2026-03-15"),
        "amount": kwargs.pop("amount", 300),
    }
    values.update(kwargs)
    doc = frappe.get_doc(values)
    doc.insert(ignore_permissions=True)
    if not do_not_submit:
        doc.submit()
    return doc


def _xlsx(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Date", "Plate", "Amount", "Reference", "Responsibility"])
    for r in rows:
        ws.append(list(r))
    buf = io.BytesIO()
    wb.save(buf)
    return save_file("fines.xlsx", buf.getvalue(), None, None, is_private=1).file_url


class TestFine(FrappeTestCase):
    def test_customer_auto_filled_from_rental(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle()
        create_vehicle_movement(vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01")
        fine = create_fine(vehicle=vehicle.name, date="2026-03-10", closing_status="Paid by Client")
        self.assertEqual(fine.customer, customer)

    def test_paid_by_client_flows_into_monthly_billing(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle()
        create_vehicle_movement(vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01")
        create_fine(vehicle=vehicle.name, date="2026-03-15", amount=300, closing_status="Paid by Client")
        sheet = create_monthly_billing(customer, "2026-03-01", do_not_submit=True)
        self.assertEqual(len(sheet.fine_lines), 1)
        self.assertEqual(sheet.total_fine_amount, 300)

    def test_deduct_from_employee(self):
        driver = create_driver()
        fine = create_fine(driver=driver.name, customer=create_customer().name, closing_status="Paid by Driver", amount=500)
        ded = create_employee_deduction(fine.name)
        self.assertEqual(frappe.db.get_value("Employee Deduction", ded, "employee"), driver.employee)
        with self.assertRaises(frappe.ValidationError):
            create_employee_deduction(fine.name)

    def test_bulk_import_creates_fines_and_routes(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle(license_plate="DXB-72001")
        create_vehicle_movement(vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01")
        f = _xlsx([("2026-03-10", "DXB-72001", 150, "F-1", "Client"), ("2026-03-12", "DXB-72001", 200, "F-2", "Company")])
        result = import_fines(f)
        self.assertEqual(result["created"], 2)
        client_fines = frappe.get_all(
            "Traffic Fine or Accident",
            filters={"vehicle": vehicle.name, "closing_status": "Paid by Client"},
        )
        self.assertEqual(len(client_fines), 1)

    def test_unmatched_plate_defaults_company(self):
        f = _xlsx([("2026-03-10", "ZZZ-00000", 150, "F-1", "")])
        result = import_fines(f)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["unmatched"], 1)
