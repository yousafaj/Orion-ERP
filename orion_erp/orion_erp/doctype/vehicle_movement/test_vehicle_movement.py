# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from orion_erp.orion_erp.doctype.vehicle_movement.vehicle_movement import demobilize
from orion_erp.tests.fixtures import (
    create_driver,
    create_vehicle,
    create_vehicle_movement,
    ensure_shift_type,
)


class TestVehicleMovement(FrappeTestCase):
	def test_mobilize_sets_vehicle_with_client(self):
		vehicle = create_vehicle()
		vm = create_vehicle_movement(vehicle=vehicle.name)
		vehicle.reload()
		self.assertEqual(vehicle.custom_state, "With Client")
		self.assertEqual(vehicle.custom_current_customer, vm.customer)
		self.assertEqual(vehicle.custom_current_rent_type, "Without Driver")
		self.assertEqual(vm.rental_status, "Active")

	def test_demobilize_frees_vehicle_and_closes_rental(self):
		vehicle = create_vehicle()
		vm = create_vehicle_movement(vehicle=vehicle.name, movement_date=add_days(nowdate(), -5))

		demobilize(vm.name, nowdate())

		vehicle.reload()
		vm.reload()
		self.assertEqual(vehicle.custom_state, "Idle")
		self.assertFalse(vehicle.custom_current_customer)
		self.assertEqual(vm.rental_status, "Closed")
		self.assertEqual(str(vm.demobilize_date), nowdate())

	def test_demobilize_twice_is_rejected(self):
		vm = create_vehicle_movement()
		demobilize(vm.name, nowdate())
		with self.assertRaises(frappe.ValidationError):
			demobilize(vm.name, nowdate())

	def test_demobilize_before_start_is_rejected(self):
		vm = create_vehicle_movement(movement_date=nowdate())
		with self.assertRaises(frappe.ValidationError):
			demobilize(vm.name, add_days(nowdate(), -3))

	def test_cancel_resets_vehicle_to_idle(self):
		vehicle = create_vehicle()
		vm = create_vehicle_movement(vehicle=vehicle.name)
		vm.cancel()
		vehicle.reload()
		self.assertEqual(vehicle.custom_state, "Idle")
		self.assertFalse(vehicle.custom_current_customer)

	def test_with_driver_requires_a_driver_row(self):
		with self.assertRaises(frappe.ValidationError):
			create_vehicle_movement(rent_type="With Driver")

	def test_with_driver_assigns_shift_and_creates_assignment(self):
		vehicle = create_vehicle()
		driver = create_driver()
		shift = ensure_shift_type()
		vm = create_vehicle_movement(
			vehicle=vehicle.name,
			rent_type="With Driver",
			driver_shifts=[{"driver": driver.name, "shift": shift}],
		)
		vehicle.reload()
		driver.reload()
		self.assertEqual(vehicle.custom_state, "With Client")
		self.assertEqual(driver.custom_state, "With Client")
		# the rental row records the created Shift Assignment
		sa = vm.driver_shifts[0].shift_assignment
		self.assertTrue(sa)
		self.assertEqual(frappe.db.get_value("Shift Assignment", sa, "employee"), driver.employee)
		# driver + vehicle child tables wired
		self.assertEqual(len(driver.custom_shifts), 1)
		self.assertEqual(len(frappe.get_doc("Vehicle", vehicle.name).custom_driver_shifts), 1)

	def test_with_driver_demobilize_releases_driver(self):
		vehicle = create_vehicle()
		driver = create_driver()
		shift = ensure_shift_type()
		vm = create_vehicle_movement(
			vehicle=vehicle.name,
			rent_type="With Driver",
			movement_date="2026-03-01",
			driver_shifts=[{"driver": driver.name, "shift": shift}],
		)
		sa = vm.driver_shifts[0].shift_assignment
		demobilize(vm.name, "2026-03-20")
		driver.reload()
		self.assertEqual(driver.custom_state, "Idle")
		self.assertEqual(frappe.db.get_value("Shift Assignment", sa, "status"), "Inactive")
		self.assertEqual(str(frappe.db.get_value("Shift Assignment", sa, "end_date")), "2026-03-20")

	def test_with_driver_rejects_more_than_two_drivers(self):
		shift = ensure_shift_type()
		d1, d2, d3 = create_driver(), create_driver(), create_driver()
		with self.assertRaises(frappe.ValidationError):
			create_vehicle_movement(
				rent_type="With Driver",
				driver_shifts=[
					{"driver": d1.name, "shift": shift},
					{"driver": d2.name, "shift": shift},
					{"driver": d3.name, "shift": shift},
				],
			)
