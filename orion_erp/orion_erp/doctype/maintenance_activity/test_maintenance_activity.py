# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from orion_erp.tests.fixtures import create_vehicle


class TestMaintenanceActivity(FrappeTestCase):
    def test_new_maintenance_activity_is_blocked(self):
        doc = frappe.get_doc(
            {"doctype": "Maintenance Activity", "vehicle": create_vehicle().name, "date": nowdate()}
        )
        with self.assertRaises(frappe.ValidationError):
            doc.insert(ignore_permissions=True)
