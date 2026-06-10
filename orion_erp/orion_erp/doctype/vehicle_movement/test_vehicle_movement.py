# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from orion_erp.orion_erp.doctype.vehicle_movement.vehicle_movement import (
    back_in_service,
    demobilize,
    to_workshop,
)
from orion_erp.tests.fixtures import (
    create_customer,
    create_driver,
    create_project,
    create_vehicle,
    create_vehicle_movement,
    create_vehicle_no_plate_code,
)


class TestVehicleMovement(FrappeTestCase):
    def test_mobilize_sets_with_client(self):
        vehicle = create_vehicle()
        vm = create_vehicle_movement(vehicle=vehicle.name)
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "With Client")
        self.assertEqual(vehicle.custom_current_customer, vm.customer)
        self.assertEqual(vm.rental_status, "Active")

    def test_plate_code_less_vehicle_mobilizes_without_crash(self):
        # Regression: the live crash "Value missing for Vehicle: Plate Code".
        vehicle = create_vehicle_no_plate_code()
        vm = create_vehicle_movement(vehicle=vehicle.name)
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "With Client")
        demobilize(vm.name, nowdate())
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Idle")

    def test_internal_movement_sets_internal_use(self):
        vehicle = create_vehicle()
        create_vehicle_movement(vehicle=vehicle.name, invoiceable=0, customer=None, project_to=None)
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Internal Use")

    def test_with_driver_sets_driver_state(self):
        vehicle = create_vehicle()
        driver = create_driver()
        create_vehicle_movement(vehicle=vehicle.name, driver=driver.name)
        driver.reload()
        self.assertEqual(driver.custom_state, "With Client")

    def test_double_booking_vehicle_blocked(self):
        vehicle = create_vehicle()
        create_vehicle_movement(vehicle=vehicle.name)  # active
        with self.assertRaises(frappe.ValidationError):
            create_vehicle_movement(vehicle=vehicle.name)  # second active → blocked

    def test_demobilize_frees_vehicle(self):
        vehicle = create_vehicle()
        vm = create_vehicle_movement(vehicle=vehicle.name, movement_date=add_days(nowdate(), -5))
        demobilize(vm.name, nowdate())
        vm.reload()
        vehicle.reload()
        self.assertEqual(vm.rental_status, "Closed")
        self.assertEqual(vehicle.custom_state, "Idle")

    def test_workshop_buttons_log_off_hire(self):
        vehicle = create_vehicle()
        vm = create_vehicle_movement(vehicle=vehicle.name, movement_date="2026-03-01")
        to_workshop(vm.name, "2026-03-10")
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Workshop")
        back_in_service(vm.name, "2026-03-14")
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "With Client")
        vm.reload()
        self.assertEqual(len(vm.off_hire), 1)
        self.assertEqual(str(vm.off_hire[0].to_date), "2026-03-14")

    def test_cancel_resets_state(self):
        vehicle = create_vehicle()
        vm = create_vehicle_movement(vehicle=vehicle.name)
        vm.cancel()
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Idle")
