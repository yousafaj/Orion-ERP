# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt
"""Workspace cleanup: the legacy 'Rental Management' delete patch + CICPA cards on Orion Fleet."""

import frappe
from frappe.tests.utils import FrappeTestCase

from orion_erp.patches.remove_rental_management_workspace import execute as remove_rm_workspace
from orion_erp.setup import ORION_FLEET_CARDS


class TestWorkspaceCleanup(FrappeTestCase):
    def test_remove_rental_management_workspace_is_idempotent(self):
        if not frappe.db.exists("Workspace", "Rental Management"):
            frappe.get_doc(
                {
                    "doctype": "Workspace",
                    "label": "Rental Management",
                    "title": "Rental Management",
                    "module": "Orion ERP",
                    "public": 1,
                    "content": "[]",
                }
            ).insert(ignore_permissions=True)
        self.assertTrue(frappe.db.exists("Workspace", "Rental Management"))

        remove_rm_workspace()
        self.assertFalse(frappe.db.exists("Workspace", "Rental Management"))

        remove_rm_workspace()  # already gone → must not raise (idempotent)

    def test_cicpa_cards_are_in_orion_fleet_list(self):
        # The CICPA expiry cards (moved off the deleted RM workspace) must stay in the canonical
        # Orion Fleet card list, or fix_orion_fleet_cards() would clobber them on migrate.
        self.assertIn("CICPAs Expiring (30 Days)", ORION_FLEET_CARDS)
        self.assertIn("Expired CICPAs", ORION_FLEET_CARDS)
