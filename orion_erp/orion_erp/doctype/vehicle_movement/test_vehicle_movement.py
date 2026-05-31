# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from orion_erp.tests.fixtures import create_project, create_vehicle


def create_vehicle_movement(vehicle=None, status="Breakdown", do_not_submit=False, **kwargs):
	"""Build a Vehicle Movement, filling the status-conditional mandatory fields.

	Mobilise needs `rent_type` + `project_to`; Demobilise needs `project_id`;
	Breakdown / Available for Use need neither.
	"""
	values = {
		"doctype": "Vehicle Movement",
		"vehicle": vehicle or create_vehicle().name,
		"status": status,
		"movement_date": kwargs.pop("movement_date", nowdate()),
	}
	if status == "Mobilise":
		values["rent_type"] = kwargs.pop("rent_type", "With Driver")
		values["project_to"] = kwargs.pop("project_to", None) or create_project().name
	elif status == "Demobilise":
		values["project_id"] = kwargs.pop("project_id", None) or create_project().name
	values.update(kwargs)

	doc = frappe.get_doc(values)
	doc.insert(ignore_permissions=True)
	if not do_not_submit:
		doc.submit()
	return doc


class TestVehicleMovement(FrappeTestCase):
	def test_mobilise_sets_vehicle_with_client(self):
		vehicle = create_vehicle()
		create_vehicle_movement(vehicle=vehicle.name, status="Mobilise")
		self.assertEqual(
			frappe.db.get_value("Vehicle", vehicle.name, "custom_state"), "With Client"
		)

	def test_demobilise_sets_vehicle_idle(self):
		vehicle = create_vehicle()
		create_vehicle_movement(vehicle=vehicle.name, status="Mobilise")
		create_vehicle_movement(vehicle=vehicle.name, status="Demobilise")
		self.assertEqual(
			frappe.db.get_value("Vehicle", vehicle.name, "custom_state"), "Idle"
		)

	def test_breakdown_sets_vehicle_workshop(self):
		vehicle = create_vehicle()
		create_vehicle_movement(vehicle=vehicle.name, status="Breakdown")
		self.assertEqual(
			frappe.db.get_value("Vehicle", vehicle.name, "custom_state"), "Workshop"
		)

	def test_cancel_resets_vehicle_to_idle(self):
		vehicle = create_vehicle()
		movement = create_vehicle_movement(vehicle=vehicle.name, status="Mobilise")
		self.assertEqual(
			frappe.db.get_value("Vehicle", vehicle.name, "custom_state"), "With Client"
		)
		movement.cancel()
		self.assertEqual(
			frappe.db.get_value("Vehicle", vehicle.name, "custom_state"), "Idle"
		)

	def test_vehicle_is_mandatory(self):
		doc = frappe.get_doc(
			{"doctype": "Vehicle Movement", "status": "Breakdown", "movement_date": nowdate()}
		)
		self.assertRaises(frappe.MandatoryError, doc.insert)
