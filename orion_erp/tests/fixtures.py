# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt
"""Shared test builders/fixtures for orion_erp.

Import these helpers in `test_*.py` files instead of hand-building documents, so
every test starts from the same baseline and only fills in the fields it cares
about. Each builder fills all *mandatory* fields with safe defaults and accepts
`**kwargs` to override any field. Submittable builders accept `do_not_submit`.

These run only on a test site (e.g. `test_orion.localhost`) — never the real site.
"""

import frappe
from frappe.utils import nowdate


# --------------------------------------------------------------------------
# Generic prerequisites
# --------------------------------------------------------------------------
def ensure_uom(name: str = "Nos") -> str:
	"""Make sure a Unit of Measure exists (Vehicle needs one)."""
	if not frappe.db.exists("UOM", name):
		frappe.get_doc({"doctype": "UOM", "uom_name": name}).insert(ignore_permissions=True)
	return name


def get_company() -> str:
	"""Return a test Company name, creating it once (reuses the HRMS helper)."""
	from hrms.tests.test_utils import create_company

	return create_company("_Test Orion Company").name


def create_project(**kwargs) -> "frappe.model.document.Document":
	doc = frappe.get_doc(
		{
			"doctype": "Project",
			"project_name": kwargs.pop("project_name", None)
			or f"_Test Project {frappe.generate_hash(length=6)}",
			"company": kwargs.pop("company", None) or get_company(),
			**kwargs,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


# --------------------------------------------------------------------------
# Fleet (vehicles / drivers)
# --------------------------------------------------------------------------
def create_vehicle(**kwargs) -> "frappe.model.document.Document":
	"""Create a Vehicle with all mandatory fields filled.

	`license_plate` is the doc name (autoname), so it is randomised to stay unique.
	"""
	ensure_uom("Nos")
	doc = frappe.get_doc(
		{
			"doctype": "Vehicle",
			"license_plate": kwargs.pop("license_plate", None) or f"_T-{frappe.generate_hash(length=8)}",
			"chassis_no": kwargs.pop("chassis_no", None) or f"_TCH-{frappe.generate_hash(length=10)}",
			"make": kwargs.pop("make", "_Test Make"),
			"model": kwargs.pop("model", "_Test Model"),
			"last_odometer": kwargs.pop("last_odometer", 0),
			"fuel_type": kwargs.pop("fuel_type", "Petrol"),
			"uom": kwargs.pop("uom", "Nos"),
			# orion_erp customizations make these mandatory on Vehicle:
			"custom_plate_code": kwargs.pop("custom_plate_code", "A"),
			"custom_ownership_status": kwargs.pop("custom_ownership_status", "Owned"),
			"custom_vehicle_type": kwargs.pop("custom_vehicle_type", "Light Vehicle"),
			**kwargs,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc
