# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from orion_erp.orion_erp.doctype.loa.loa import auto_expire_loas
from orion_erp.tests.fixtures import create_loa, create_location


class TestLOA(FrappeTestCase):
	def test_location_code_is_filled_from_location(self):
		loc = create_location(custom_location_code="LC-XYZ")
		loa = create_loa(do_not_submit=True, locations=[{"location": loc.name}])
		self.assertEqual(loa.locations[0].location_code, "LC-XYZ")

	def test_missing_location_code_is_rejected(self):
		loc = create_location(custom_location_code="")
		with self.assertRaises(frappe.ValidationError):
			create_loa(do_not_submit=True, locations=[{"location": loc.name}])

	def test_typed_location_code_is_saved_back_to_location(self):
		loc = create_location(custom_location_code="")  # no code on the master
		create_loa(do_not_submit=True, locations=[{"location": loc.name, "location_code": "NEW-1"}])
		# the code typed on the LOA row is written back to the Location master
		self.assertEqual(frappe.db.get_value("Location", loc.name, "custom_location_code"), "NEW-1")

	def test_auto_expire_marks_past_dated_active_loa_expired(self):
		loa = create_loa(expiry_date=add_days(nowdate(), -1))  # submitted + Active + expired
		self.assertEqual(loa.loa_status, "Active")

		auto_expire_loas()

		loa.reload()
		self.assertEqual(loa.loa_status, "Expired")
		self.assertEqual(loa.active, 0)

	def test_auto_expire_leaves_future_dated_loa_active(self):
		loa = create_loa(expiry_date=add_days(nowdate(), 30))

		auto_expire_loas()

		loa.reload()
		self.assertEqual(loa.loa_status, "Active")
