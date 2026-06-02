# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from orion_erp.orion_erp.doctype.loa.loa import auto_expire_loas
from orion_erp.tests.fixtures import create_loa


class TestLOA(FrappeTestCase):
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
