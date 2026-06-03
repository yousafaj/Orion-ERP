# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from orion_erp.tests.fixtures import (
    create_driver,
    create_project,
    create_vehicle,
    ensure_shift_type,
)


class TestDriverMovement(FrappeTestCase):
    """Driver Movement is deprecated — driver assignment now lives on Vehicle
    Movement (the shared shift engine in driver_movement.utils is exercised by
    test_vehicle_movement's With-Driver tests)."""

    def test_new_driver_movement_is_blocked(self):
        driver = create_driver()
        doc = frappe.get_doc(
            {
                "doctype": "Driver Movement",
                "date": nowdate(),
                "mobilization_status": "Mobilize",
                "driver": driver.name,
                "vehicle": create_vehicle().name,
                "project": create_project().name,
                "shift": ensure_shift_type(),
            }
        )
        with self.assertRaises(frappe.ValidationError):
            doc.insert(ignore_permissions=True)
