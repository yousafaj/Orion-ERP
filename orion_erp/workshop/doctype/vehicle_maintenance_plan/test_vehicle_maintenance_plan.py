from frappe.tests.utils import FrappeTestCase

from orion_erp.tests.fixtures import create_vehicle, get_company


class TestVehicleMaintenancePlan(FrappeTestCase):
    def test_date_and_odometer_next_due_values(self):
        import frappe

        vehicle = create_vehicle(custom_ownership_status="Rented")
        plan = frappe.get_doc(
            {
                "doctype": "Vehicle Maintenance Plan",
                "company": get_company(),
                "vehicle": vehicle.name,
                "maintenance_type": "Periodic Service",
                "schedule_basis": "Date and Odometer",
                "interval_days": 90,
                "interval_km": 5000,
                "last_service_date": "2026-09-01",
                "last_service_odometer": 10000,
            }
        ).insert(ignore_permissions=True)

        self.assertEqual(str(plan.next_due_date), "2026-11-30")
        self.assertEqual(plan.next_due_odometer, 15000)
        self.assertFalse(plan.asset)
