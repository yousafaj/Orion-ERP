# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt
#
# TEMPLATE — copy this into a doctype folder as `test_<doctype>.py` when you add
# a new doctype with controller logic, then replace the placeholders. Reuse the
# shared builders in `orion_erp/tests/fixtures.py` instead of hand-building docs.
#
# Run it on the TEST site only (never orion.localhost):
#   bench --site test_orion.localhost run-tests --doctype "Your Doctype"
#
# This file is intentionally inert (no `def test_` methods) so it is not collected
# as a real test — it's documentation/scaffolding.

import frappe  # noqa: F401
from frappe.tests.utils import FrappeTestCase  # noqa: F401

# from orion_erp.tests.fixtures import create_vehicle, create_loa  # etc.


class _TemplateExample:
	"""Rename to TestYourDoctype(FrappeTestCase) and uncomment the methods.

	Patterns to cover for a typical submittable doctype:

	    def test_validation_rejects_bad_input(self):
	        doc = make_doc(some_field=BAD_VALUE, do_not_submit=True)
	        with self.assertRaises(frappe.ValidationError):
	            doc.insert()

	    def test_on_submit_side_effect(self):
	        doc = make_doc()                      # builds + submits
	        related = frappe.db.get_value("Other", doc.link, "state")
	        self.assertEqual(related, "Expected")

	    def test_on_cancel_reverses_side_effect(self):
	        doc = make_doc()
	        doc.cancel()
	        self.assertEqual(frappe.db.get_value("Other", doc.link, "state"), "Reverted")
	"""
