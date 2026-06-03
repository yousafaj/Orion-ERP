# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from orion_erp.orion_erp.doctype.traffic_fine_or_accident.traffic_fine_or_accident import (
    create_employee_deduction,
)
from orion_erp.tests.fixtures import (
    create_customer,
    create_driver,
    create_monthly_billing,
    create_project,
    create_vehicle,
    create_vehicle_movement,
)


def create_traffic_fine(do_not_submit=False, **kwargs):
    customer = kwargs.pop("customer", None)
    project = kwargs.pop("project", None)
    if not project:
        if not customer:
            customer = create_customer().name
        project = create_project(customer=customer).name
    if not customer and project:
        customer = frappe.db.get_value("Project", project, "customer")
    values = {
        "doctype": "Traffic Fine or Accident",
        "vehicle": kwargs.pop("vehicle", None) or create_vehicle().name,
        "customer": customer,
        "project": project,
        "date": kwargs.pop("date", "2026-03-15"),
        "evidence": kwargs.pop("evidence", "/files/evidence.pdf"),
        "detail": kwargs.pop("detail", [{"fine_number": "F-1", "amount": 300}]),
    }
    values.update(kwargs)
    doc = frappe.get_doc(values)
    doc.insert(ignore_permissions=True)
    if not do_not_submit:
        doc.submit()
    return doc


class TestTrafficFineorAccident(FrappeTestCase):
    def test_total_amount_summed_from_details(self):
        fine = create_traffic_fine(
            detail=[{"fine_number": "F1", "amount": 100}, {"fine_number": "F2", "amount": 250}],
            do_not_submit=True,
        )
        self.assertEqual(fine.total_amount, 350)

    def test_submit_requires_evidence(self):
        with self.assertRaises(frappe.ValidationError):
            create_traffic_fine(evidence=None)

    def test_responsibility_closes_record(self):
        fine = create_traffic_fine()
        self.assertEqual(fine.status, "Open")  # stays open until Accounts act
        fine.db_set("closing_status", "Paid by Company")
        fine.run_method("on_update_after_submit")
        fine.reload()
        self.assertEqual(fine.status, "Closed")

    def test_paid_by_client_flows_into_monthly_billing(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        create_traffic_fine(
            customer=customer,
            project=project,
            date="2026-03-15",
            closing_status="Paid by Client",
            detail=[{"fine_number": "F1", "amount": 300}],
        )
        sheet = create_monthly_billing(customer, "2026-03-01", do_not_submit=True)
        self.assertEqual(len(sheet.fine_lines), 1)
        self.assertEqual(sheet.fine_lines[0].amount, 300)
        self.assertEqual(sheet.total_fine_amount, 300)

    def test_paid_by_company_not_billed(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        create_traffic_fine(
            customer=customer, project=project, date="2026-03-15", closing_status="Paid by Company"
        )
        sheet = create_monthly_billing(customer, "2026-03-01", do_not_submit=True)
        self.assertEqual(len(sheet.fine_lines), 0)

    def test_deduct_from_employee_creates_draft_deduction(self):
        driver = create_driver()
        fine = create_traffic_fine(
            driver=driver.name, closing_status="Paid by Driver", detail=[{"fine_number": "F1", "amount": 500}]
        )
        ded_name = create_employee_deduction(fine.name)
        ded = frappe.get_doc("Employee Deduction", ded_name)
        self.assertEqual(ded.employee, driver.employee)
        self.assertEqual(ded.docstatus, 0)
        fine.reload()
        self.assertEqual(fine.employee_deduction, ded_name)
        # second call is rejected (already created)
        with self.assertRaises(frappe.ValidationError):
            create_employee_deduction(fine.name)

    def test_deduct_only_for_driver_responsibility(self):
        fine = create_traffic_fine(closing_status="Paid by Client")
        with self.assertRaises(frappe.ValidationError):
            create_employee_deduction(fine.name)

    def test_customer_auto_filled_from_rental(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle()
        create_vehicle_movement(
            vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01"
        )
        # do NOT pass customer/project — they should auto-fill from the rental
        fine = frappe.get_doc(
            {
                "doctype": "Traffic Fine or Accident",
                "vehicle": vehicle.name,
                "date": "2026-03-10",
                "evidence": "/files/e.pdf",
                "detail": [{"fine_number": "F1", "amount": 200}],
            }
        ).insert(ignore_permissions=True)
        self.assertEqual(fine.customer, customer)
