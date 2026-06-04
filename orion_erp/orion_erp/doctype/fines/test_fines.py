# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import io

import frappe
import openpyxl
from frappe.tests.utils import FrappeTestCase
from frappe.utils.file_manager import save_file

from orion_erp.orion_erp.doctype.fines.fines import (
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

# Header layout of the real RTA fines portal export (subset the importer reads).
_FINE_HEADER = [
    "Fine Number",
    "Status",
    "Plate Number",
    "Date",
    "Amount",
    "Fine Location",
    "Fine Description",
]


def create_fine(do_not_submit=False, **kwargs):
    values = {
        "doctype": "Fines",
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


def _portal_fine_xlsx(rows):
    """Build a workbook mirroring the portal fines export (rows are dicts keyed like _FINE_HEADER)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(_FINE_HEADER)
    for r in rows:
        ws.append([r.get(h) for h in _FINE_HEADER])
    buf = io.BytesIO()
    wb.save(buf)
    return save_file("fines.xlsx", buf.getvalue(), None, None, is_private=1).file_url


def _fine_row(fine_number, plate, amount, date, status="Payable", location="", description=""):
    return {
        "Fine Number": fine_number,
        "Status": status,
        "Plate Number": plate,
        "Date": date,
        "Amount": amount,
        "Fine Location": location,
        "Fine Description": description,
    }


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

    def test_bulk_import_parses_portal_export(self):
        """Portal columns map correctly, ' AED x ' amounts are cleaned, detail + status captured."""
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle(license_plate="72001")
        create_vehicle_movement(vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01")

        f = _portal_fine_xlsx(
            [
                _fine_row(
                    "F-1", "72001", " AED 500.00 ", "2026-03-10 2:07:59",
                    location="Abu Dhabi-Al Nouf", description="Exceeding speed limit",
                ),
                _fine_row("F-2", "72001", " AED 1,000.00 ", "2026-03-12 9:00:00", status="Unpayable"),
            ]
        )
        result = import_fines(f)
        self.assertEqual(result["created"], 2)

        f1 = frappe.get_doc("Fines", frappe.db.get_value("Fines", {"ref_no": "F-1"}))
        self.assertEqual(f1.amount, 500)  # " AED 500.00 " cleaned
        self.assertEqual(f1.vehicle, vehicle.name)  # plate number → vehicle
        self.assertEqual(f1.closing_status, "Paid by Client")  # has a rental
        self.assertEqual(f1.portal_status, "Payable")
        self.assertEqual(f1.fine_description, "Exceeding speed limit")
        self.assertEqual(f1.fine_location, "Abu Dhabi-Al Nouf")

        # Unpayable rows are imported too (decision: import all rows); commas stripped.
        f2 = frappe.get_doc("Fines", frappe.db.get_value("Fines", {"ref_no": "F-2"}))
        self.assertEqual(f2.amount, 1000)
        self.assertEqual(f2.portal_status, "Unpayable")

    def test_reimport_skips_duplicates_by_ref_no(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle(license_plate="72005")
        create_vehicle_movement(vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01")
        rows = [_fine_row("F-DUP", "72005", " AED 300.00 ", "2026-03-10 8:00:00")]
        self.assertEqual(import_fines(_portal_fine_xlsx(rows))["created"], 1)
        second = import_fines(_portal_fine_xlsx(rows))
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(frappe.db.count("Fines", {"ref_no": "F-DUP"}), 1)

    def test_unmatched_plate_defaults_company(self):
        f = _portal_fine_xlsx([_fine_row("F-X", "00000", " AED 150.00 ", "2026-03-10 8:00:00")])
        result = import_fines(f)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["unmatched"], 1)
