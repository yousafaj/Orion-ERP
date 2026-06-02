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
from frappe.utils import add_days, nowdate


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


# --------------------------------------------------------------------------
# Parties / locations (prerequisites for LOA + CICPA)
# --------------------------------------------------------------------------
def ensure_customer_group(name: str = "_Test Orion Customer Group") -> str:
	"""erpnext rejects 'group' Customer Groups on a Customer, so make a leaf one."""
	if not frappe.db.exists("Customer Group", name):
		frappe.get_doc(
			{
				"doctype": "Customer Group",
				"customer_group_name": name,
				"parent_customer_group": "All Customer Groups",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
	return name


def create_customer(**kwargs) -> "frappe.model.document.Document":
	doc = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": kwargs.pop("customer_name", None) or f"_Test Customer {frappe.generate_hash(length=6)}",
			"customer_type": kwargs.pop("customer_type", "Company"),
			"customer_group": kwargs.pop("customer_group", None) or ensure_customer_group(),
			"territory": kwargs.pop("territory", "All Territories"),
			**kwargs,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def create_location(**kwargs) -> "frappe.model.document.Document":
	doc = frappe.get_doc(
		{
			"doctype": "Location",
			"location_name": kwargs.pop("location_name", None) or f"_Test Location {frappe.generate_hash(length=6)}",
			**kwargs,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def create_contract_authority(name: str | None = None, **kwargs) -> "frappe.model.document.Document":
	"""Contract Authority uses prompt autoname, so the name is supplied directly."""
	name = name or f"_Test Authority {frappe.generate_hash(length=6)}"
	if frappe.db.exists("Contract Authority", name):
		return frappe.get_doc("Contract Authority", name)
	doc = frappe.new_doc("Contract Authority")
	doc.name = name
	doc.update(kwargs)
	doc.insert(ignore_permissions=True)
	return doc


# --------------------------------------------------------------------------
# LOA (license of authority — holds the CICPA quotas)
# --------------------------------------------------------------------------
def create_loa(do_not_submit: bool = False, **kwargs) -> "frappe.model.document.Document":
	"""Create an LOA. Defaults to a generous quota and an active, dated record.

	Pass `do_not_submit=True` when a draft LOA is wanted (e.g. so CICPA.on_submit
	can freely `loa.save()` the running counters).
	"""
	quota = kwargs.pop("quota", 10)
	values = {
		"doctype": "LOA",
		"issuing_authority": kwargs.pop("issuing_authority", None) or create_customer().name,
		"end_user": kwargs.pop("end_user", None) or create_contract_authority().name,
		"issue_date": kwargs.pop("issue_date", add_days(nowdate(), -10)),
		"expiry_date": kwargs.pop("expiry_date", add_days(nowdate(), 365)),
		"ref_no": kwargs.pop("ref_no", None) or f"_T-REF-{frappe.generate_hash(length=6)}",
		"contract_number": kwargs.pop("contract_number", None) or f"_T-CN-{frappe.generate_hash(length=6)}",
		"total_vehicle_quota": kwargs.pop("total_vehicle_quota", quota),
		"total_driver_quota": kwargs.pop("total_driver_quota", quota),
		"remaining_vehicle_quota": kwargs.pop("remaining_vehicle_quota", quota),
		"remaining_driver_quota": kwargs.pop("remaining_driver_quota", quota),
		"allocated_vehicle_quota": kwargs.pop("allocated_vehicle_quota", 0),
		"allocated_driver_quota": kwargs.pop("allocated_driver_quota", 0),
		"loa_status": kwargs.pop("loa_status", "Active"),
		"active": kwargs.pop("active", 1),
		"locations": kwargs.pop("locations", None) or [{"location": create_location().name}],
	}
	values.update(kwargs)
	doc = frappe.get_doc(values)
	doc.insert(ignore_permissions=True)
	if not do_not_submit:
		doc.submit()
	return doc
