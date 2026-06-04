# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, get_first_day, getdate, nowdate

from orion_erp.orion_erp.doctype.monthly_billing.monthly_billing import (
    billable_days,
    build_monthly_billing,
    create_monthly_billing_sheets,
    mark_invoiced,
    period_covers,
    rental_customer,
    rental_on_date,
)
from orion_erp.tests.fixtures import (
    create_customer,
    create_monthly_billing,
    create_project,
    create_vehicle,
    create_vehicle_movement,
)


class TestBillableDaysHelper(FrappeTestCase):
    def test_partial_first_month_from_5th(self):
        # March 2026 has 31 days; mobilized on the 5th, still out -> 27 days.
        self.assertEqual(billable_days("2026-03-05", None, "2026-03-01", "2026-03-31"), 27)

    def test_full_month_when_spanning(self):
        self.assertEqual(billable_days("2026-01-10", "2026-05-20", "2026-03-01", "2026-03-31"), 31)

    def test_partial_last_month_on_demobilize(self):
        self.assertEqual(billable_days("2026-01-10", "2026-03-20", "2026-03-01", "2026-03-31"), 20)

    def test_zero_when_outside_month(self):
        self.assertEqual(billable_days("2026-04-01", None, "2026-03-01", "2026-03-31"), 0)

    def test_period_covers(self):
        self.assertTrue(period_covers("2026-03-05", None, "2026-03-20"))
        self.assertTrue(period_covers("2026-03-05", "2026-03-25", "2026-03-20"))
        self.assertFalse(period_covers("2026-03-05", "2026-03-25", "2026-03-26"))
        self.assertFalse(period_covers("2026-03-05", None, "2026-03-04"))


class TestRentalOnDate(FrappeTestCase):
    def test_rental_on_date_and_customer(self):
        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle()
        create_vehicle_movement(
            vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01"
        )
        r = rental_on_date(vehicle.name, "2026-03-15")
        self.assertIsNotNone(r)
        self.assertEqual(r.customer, customer)
        self.assertEqual(rental_customer(vehicle.name, "2026-03-15")["customer"], customer)

    def test_no_rental_returns_none(self):
        vehicle = create_vehicle()
        self.assertIsNone(rental_on_date(vehicle.name, "2026-03-15"))
        self.assertEqual(rental_customer(vehicle.name, "2026-03-15"), {})


class TestMonthlyBilling(FrappeTestCase):
    def _customer_with_project(self):
        customer = create_customer()
        project = create_project(customer=customer.name)
        return customer.name, project.name

    def test_build_prorates_first_month(self):
        customer, project = self._customer_with_project()
        vehicle = create_vehicle()
        create_vehicle_movement(
            vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-05"
        )
        sheet = create_monthly_billing(customer, "2026-03-10", do_not_submit=True)
        self.assertEqual(len(sheet.vehicle_lines), 1)
        line = sheet.vehicle_lines[0]
        self.assertEqual(line.vehicle, vehicle.name)
        self.assertEqual(line.billable_days, 27)
        self.assertEqual(line.days_in_month, 31)
        self.assertEqual(sheet.total_vehicle_days, 27)
        # billing_month snapped to the 1st, label derived
        self.assertEqual(str(sheet.billing_month), "2026-03-01")
        self.assertEqual(sheet.month_label, "2026-03")

    def test_build_is_idempotent(self):
        customer, project = self._customer_with_project()
        vehicle = create_vehicle()
        create_vehicle_movement(
            vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-05"
        )
        sheet = create_monthly_billing(customer, "2026-03-01", do_not_submit=True)
        sheet.build()
        self.assertEqual(len(sheet.vehicle_lines), 1)
        self.assertEqual(sheet.total_vehicle_days, 27)

    def test_duplicate_customer_month_rejected(self):
        customer, _ = self._customer_with_project()
        create_monthly_billing(customer, "2026-03-01")
        with self.assertRaises(frappe.ValidationError):
            create_monthly_billing(customer, "2026-03-20")

    def test_mark_invoiced_requires_ref_and_sets_flag(self):
        customer, _ = self._customer_with_project()
        sheet = create_monthly_billing(customer, "2026-03-01")
        mark_invoiced(sheet.name, "2026-04-02", "INV-001")
        sheet.reload()
        self.assertTrue(sheet.invoiced)
        self.assertEqual(str(sheet.invoiced_date), "2026-04-02")
        self.assertEqual(sheet.external_invoice_ref, "INV-001")
        # already invoiced -> rejected
        with self.assertRaises(frappe.ValidationError):
            mark_invoiced(sheet.name, "2026-04-03", "INV-002")

    def test_build_monthly_billing_creates_and_submits(self):
        customer, project = self._customer_with_project()
        vehicle = create_vehicle()
        create_vehicle_movement(
            vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-02-01"
        )
        name = build_monthly_billing(customer, "2026-02-15")
        doc = frappe.get_doc("Monthly Billing", name)
        self.assertEqual(doc.docstatus, 1)
        self.assertEqual(doc.total_vehicle_days, 28)  # Feb 2026, full month

    def test_refresh_picks_up_rental_added_after_submit(self):
        from orion_erp.orion_erp.doctype.monthly_billing.monthly_billing import build as refresh

        customer, project = self._customer_with_project()
        sheet = create_monthly_billing(customer, "2026-03-01")  # submitted, no rentals yet
        self.assertEqual(sheet.total_vehicle_days, 0)
        vehicle = create_vehicle()
        create_vehicle_movement(
            vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01"
        )
        refresh(sheet.name)  # Refresh Lines on a submitted (not-invoiced) sheet
        sheet.reload()
        self.assertEqual(sheet.total_vehicle_days, 31)  # March, full month

    def test_off_hire_days_excluded_from_billing(self):
        from orion_erp.orion_erp.doctype.vehicle_movement.vehicle_movement import (
            back_in_service,
            to_workshop,
        )

        customer, project = self._customer_with_project()
        vehicle = create_vehicle()
        vm = create_vehicle_movement(
            vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01"
        )
        to_workshop(vm.name, "2026-03-10")
        back_in_service(vm.name, "2026-03-14")  # 5 off-hire days (10-14 incl.)
        sheet = create_monthly_billing(customer, "2026-03-01", do_not_submit=True)
        # March full month (31) for an ongoing rental, minus 5 workshop days = 26
        self.assertEqual(sheet.vehicle_lines[0].billable_days, 26)

    def test_month_close_job_creates_submitted_sheet(self):
        prev_month = get_first_day(add_months(getdate(nowdate()), -1))
        customer, project = self._customer_with_project()
        vehicle = create_vehicle()
        create_vehicle_movement(
            vehicle=vehicle.name,
            customer=customer,
            project_to=project,
            movement_date=add_days(prev_month, 1),  # active in the just-closed month
        )
        create_monthly_billing_sheets()
        name = frappe.db.get_value(
            "Monthly Billing", {"customer": customer, "billing_month": prev_month}
        )
        self.assertTrue(name)
        self.assertEqual(frappe.db.get_value("Monthly Billing", name, "docstatus"), 1)
