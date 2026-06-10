# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from orion_erp.tasks.daily import deactivate_expired_vehicles
from orion_erp.tests.fixtures import create_vehicle


class TestDailyVehicleDeactivation(FrappeTestCase):
    def test_rented_vehicle_past_rent_end_is_deactivated(self):
        vehicle = create_vehicle(
            custom_ownership_status="Rented",
            custom_rent_start_date=add_days(nowdate(), -100),
            custom_rent_end_date=add_days(nowdate(), -5),
        )
        deactivate_expired_vehicles()
        vehicle.reload()
        self.assertEqual(vehicle.custom_status, "Inactive")

    def test_rented_vehicle_with_future_rent_end_stays_active(self):
        vehicle = create_vehicle(
            custom_ownership_status="Rented",
            custom_rent_start_date=add_days(nowdate(), -10),
            custom_rent_end_date=add_days(nowdate(), 30),
        )
        deactivate_expired_vehicles()
        vehicle.reload()
        self.assertEqual(vehicle.custom_status, "Active")

    def test_owned_vehicle_without_sold_asset_stays_active(self):
        vehicle = create_vehicle(custom_ownership_status="Owned")
        deactivate_expired_vehicles()
        vehicle.reload()
        self.assertEqual(vehicle.custom_status, "Active")
