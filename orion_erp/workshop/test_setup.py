import frappe
from frappe.tests.utils import FrappeTestCase

from orion_erp.workshop.setup import (
    VEHICLE_PERMISSION_FIELDS,
    WORKSHOP_ROLES,
    ensure_vehicle_read_only_permissions,
)


class TestWorkshopSetup(FrappeTestCase):
    def test_workshop_roles_have_vehicle_read_select_only(self):
        ensure_vehicle_read_only_permissions()

        for role_name in WORKSHOP_ROLES:
            permissions = frappe.get_all(
                "Custom DocPerm",
                filters={
                    "parent": "Vehicle",
                    "role": role_name,
                    "permlevel": 0,
                },
                fields=["name", *VEHICLE_PERMISSION_FIELDS],
            )

            self.assertTrue(permissions)
            for permission in permissions:
                self.assertEqual(permission.read, 1)
                self.assertEqual(permission.select, 1)
                for fieldname in VEHICLE_PERMISSION_FIELDS:
                    if fieldname in {"read", "select"}:
                        continue
                    self.assertEqual(permission.get(fieldname), 0)
