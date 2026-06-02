# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from orion_erp.orion_erp.doctype.cicpa.cicpa import auto_expire_cicpas, mark_cicpa_status
from orion_erp.tests.fixtures import create_loa


def create_cicpa(loa=None, cicpa_type="Vehicle", do_not_submit=False, **kwargs):
	"""Build a CICPA against an LOA. Uses a *draft* LOA by default so that
	CICPA.on_submit can update the LOA's running counters."""
	loa = loa or create_loa(do_not_submit=True).name
	values = {
		"doctype": "CICPA",
		"loa": loa,
		"cicpa_type": cicpa_type,
		"cicpa_status": kwargs.pop("cicpa_status", "Active"),
		"issue_date": kwargs.pop("issue_date", nowdate()),
		"expiry_date": kwargs.pop("expiry_date", add_days(nowdate(), 365)),
	}
	values.update(kwargs)
	doc = frappe.get_doc(values)
	doc.insert(ignore_permissions=True)
	if not do_not_submit:
		doc.submit()
	return doc


class TestCICPA(FrappeTestCase):
	def test_validate_throws_when_vehicle_quota_exhausted(self):
		loa = create_loa(do_not_submit=True, total_vehicle_quota=1, remaining_vehicle_quota=0)
		with self.assertRaises(frappe.ValidationError):
			create_cicpa(loa=loa.name, cicpa_type="Vehicle", do_not_submit=True)

	def test_on_submit_increments_loa_created_counter(self):
		loa = create_loa(do_not_submit=True)
		create_cicpa(loa=loa.name, cicpa_type="Vehicle")
		loa.reload()
		self.assertEqual(loa.total_created_vehicle_cicpa, 1)

	def test_mark_status_expired_frees_the_quota(self):
		loa = create_loa(do_not_submit=True)
		cicpa = create_cicpa(loa=loa.name, cicpa_type="Vehicle")
		loa.reload()
		self.assertEqual(loa.total_created_vehicle_cicpa, 1)

		mark_cicpa_status(cicpa.name, "Expired")

		cicpa.reload()
		loa.reload()
		self.assertEqual(cicpa.cicpa_status, "Expired")
		self.assertEqual(loa.total_created_vehicle_cicpa, 0)

	def test_mark_status_rejects_double_transition(self):
		loa = create_loa(do_not_submit=True)
		cicpa = create_cicpa(loa=loa.name, cicpa_type="Vehicle")
		mark_cicpa_status(cicpa.name, "Expired")
		# already Expired -> a second transition must be rejected
		with self.assertRaises(frappe.ValidationError):
			mark_cicpa_status(cicpa.name, "Cancelled")

	def test_auto_expire_marks_past_dated_cicpa_expired(self):
		loa = create_loa(do_not_submit=True)
		cicpa = create_cicpa(loa=loa.name, cicpa_type="Vehicle", expiry_date=add_days(nowdate(), -1))

		auto_expire_cicpas()

		cicpa.reload()
		self.assertEqual(cicpa.cicpa_status, "Expired")
