# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from orion_erp.orion_erp.doctype.maintenance_activity.maintenance_activity import return_to_service
from orion_erp.tests.fixtures import create_vehicle, create_vehicle_movement


def create_maintenance_activity(vehicle=None, do_not_submit=False, **kwargs):
    values = {
        "doctype": "Maintenance Activity",
        "vehicle": vehicle or create_vehicle().name,
        "date": kwargs.pop("date", nowdate()),
    }
    values.update(kwargs)
    doc = frappe.get_doc(values)
    doc.insert(ignore_permissions=True)
    if not do_not_submit:
        doc.submit()
    return doc


class TestMaintenanceActivity(FrappeTestCase):
    def test_submit_sets_vehicle_workshop(self):
        vehicle = create_vehicle()
        create_maintenance_activity(vehicle=vehicle.name)
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Workshop")

    def test_return_to_service_idle_when_no_rental(self):
        vehicle = create_vehicle()
        ma = create_maintenance_activity(vehicle=vehicle.name)
        return_to_service(ma.name)
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Idle")

    def test_return_to_service_restores_with_client_when_rented(self):
        vehicle = create_vehicle()
        create_vehicle_movement(vehicle=vehicle.name)  # vehicle now With Client
        ma = create_maintenance_activity(vehicle=vehicle.name)  # -> Workshop
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Workshop")
        return_to_service(ma.name)
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "With Client")

    def test_cancel_restores_state(self):
        vehicle = create_vehicle()
        ma = create_maintenance_activity(vehicle=vehicle.name)
        ma.cancel()
        vehicle.reload()
        self.assertEqual(vehicle.custom_state, "Idle")

    def test_customer_auto_filled_from_rental(self):
        from orion_erp.tests.fixtures import (
            create_customer,
            create_project,
            create_vehicle_movement,
        )

        customer = create_customer().name
        project = create_project(customer=customer).name
        vehicle = create_vehicle()
        create_vehicle_movement(
            vehicle=vehicle.name, customer=customer, project_to=project, movement_date="2026-03-01"
        )
        ma = frappe.get_doc(
            {"doctype": "Maintenance Activity", "vehicle": vehicle.name, "date": "2026-03-10"}
        ).insert(ignore_permissions=True)
        self.assertEqual(ma.customer, customer)
