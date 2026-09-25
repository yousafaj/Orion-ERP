import frappe
from frappe.tests.utils import FrappeTestCase

from orion_erp.tests.fixtures import create_vehicle, ensure_uom, get_company


def ensure_test_item():
    item_code = "_Test Workshop Item"
    if not frappe.db.exists("Item", item_code):
        ensure_uom("Nos")
        frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item_code,
                "item_group": "All Item Groups",
                "stock_uom": "Nos",
                "is_stock_item": 0,
            }
        ).insert(ignore_permissions=True)
    return item_code


def create_job(vehicle=None, **kwargs):
    vehicle = vehicle or create_vehicle().name
    values = {
        "doctype": "Workshop Job Card",
        "company": get_company(),
        "vehicle": vehicle,
        "status": "Inspection",
    }
    values.update(kwargs)
    return frappe.get_doc(values).insert(ignore_permissions=True)


class TestWorkshopJobCard(FrappeTestCase):
    def test_rented_vehicle_does_not_require_asset(self):
        vehicle = create_vehicle(custom_ownership_status="Rented")
        job = create_job(vehicle.name)
        self.assertEqual(job.vehicle, vehicle.name)
        self.assertFalse(job.asset)

    def test_only_one_active_job_per_vehicle(self):
        vehicle = create_vehicle()
        create_job(vehicle.name)
        with self.assertRaises(frappe.ValidationError):
            create_job(vehicle.name)

    def test_costs_are_calculated_without_accounting_posting(self):
        job = create_job(
            parts=[{"item_code": ensure_test_item(), "qty": 2, "rate": 25}],
            tasks=[{"subject": "Test task", "labour_cost": 40}],
            external_services=[{"description": "Test external service", "amount": 30}],
            overhead_cost=10,
            internal_charge=150,
        )
        self.assertEqual(job.parts_cost, 50)
        self.assertEqual(job.labour_cost, 40)
        self.assertEqual(job.external_cost, 30)
        self.assertEqual(job.actual_cost, 130)
        self.assertEqual(job.charge_variance, 20)

    def test_vehicle_state_is_restored_on_release(self):
        vehicle = create_vehicle(custom_state="Idle")
        job = create_job(vehicle.name)
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Workshop")

        for status in (
            "Estimate",
            "Approved",
            "In Progress",
            "Work Completed",
            "Quality Control",
            "Ready for Release",
            "Released",
        ):
            job.status = status
            job.save(ignore_permissions=True)

        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Idle")
