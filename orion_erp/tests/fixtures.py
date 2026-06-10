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


def ensure_warehouse_type(name: str = "Transit") -> str:
	"""erpnext's Company.on_update auto-creates warehouses that link Warehouse Type
	"Transit", which ships only in the setup-wizard fixtures. Ensure it on fresh sites."""
	if not frappe.db.exists("Warehouse Type", name):
		wt = frappe.new_doc("Warehouse Type")
		wt.name = name
		wt.insert(ignore_permissions=True)
	return name


def get_company() -> str:
	"""Return a test Company name, creating it once (reuses the HRMS helper)."""
	from hrms.tests.test_utils import create_company

	ensure_warehouse_type("Transit")
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


def ensure_nationality(name: str = "_Test Nationality") -> str:
	if not frappe.db.exists("Nationality", name):
		doc = frappe.new_doc("Nationality")
		doc.name = name  # Nationality uses prompt naming
		doc.insert(ignore_permissions=True)
	return name


def ensure_employee_certificate(name: str = "Passport no") -> str:
	"""orion_erp's employee validation requires a 'Passport no' certificate. The
	cert name is a Link to 'Employee Certificate'."""
	if not frappe.db.exists("Employee Certificate", name):
		# Employee Certificate is named by its `type_name` field.
		frappe.get_doc({"doctype": "Employee Certificate", "type_name": name}).insert(ignore_permissions=True)
	return name


def ensure_shift_type(name: str = "_Test Day Shift") -> str:
	if not frappe.db.exists("Shift Type", name):
		frappe.get_doc(
			{
				"doctype": "Shift Type",
				"name": name,
				"start_time": "08:00:00",
				"end_time": "17:00:00",
			}
		).insert(ignore_permissions=True)
	return name


def create_employee(**kwargs) -> "frappe.model.document.Document":
	"""Create a minimal orion-valid Employee (carries the required 'Passport no'
	certificate so orion's employee validation passes)."""
	ensure_employee_certificate("Passport no")
	doc = frappe.get_doc(
		{
			"doctype": "Employee",
			"first_name": kwargs.pop("first_name", None) or f"_Test Emp {frappe.generate_hash(length=5)}",
			"gender": kwargs.pop("gender", "Male"),
			"date_of_birth": kwargs.pop("date_of_birth", "1990-01-01"),
			"date_of_joining": kwargs.pop("date_of_joining", "2020-01-01"),
			"company": kwargs.pop("company", None) or get_company(),
			"custom_nationality": kwargs.pop("custom_nationality", None) or ensure_nationality(),
			"custom_total_salary_as_per_offer_letter": kwargs.pop(
				"custom_total_salary_as_per_offer_letter", "0"
			),
			"custom_certificates": kwargs.pop(
				"custom_certificates",
				[
					{
						"certification_name": "Passport no",
						"reference_no": f"P-{frappe.generate_hash(length=6)}",
						"date_of_issue": "2020-01-01",
						"date_of_expiry": "2030-01-01",
					}
				],
			),
			**kwargs,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def create_driver(**kwargs) -> "frappe.model.document.Document":
	"""Create an ERPNext Driver linked to a fresh orion Employee."""
	employee = kwargs.pop("employee", None) or create_employee().name
	nationality = frappe.db.get_value("Employee", employee, "custom_nationality") or ensure_nationality()
	doc = frappe.get_doc(
		{
			"doctype": "Driver",
			"full_name": kwargs.pop("full_name", None) or f"_Test Driver {frappe.generate_hash(length=5)}",
			"employee": employee,
			"custom_nationality": kwargs.pop("custom_nationality", None) or nationality,
			"status": kwargs.pop("status", "Active"),
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


def ensure_location_custom_field() -> None:
	"""orion_erp's `LOA locations cdt.location_code` fetches from
	`location.custom_location_code`, but the app does not ship that Custom Field
	(a real orion_erp bug — fresh installs break on LOA creation). Recreate it so
	tests mirror a correctly-set-up site.
	"""
	if not frappe.db.exists("Custom Field", {"dt": "Location", "fieldname": "custom_location_code"}):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Location",
				"fieldname": "custom_location_code",
				"label": "Location Code",
				"fieldtype": "Data",
				"insert_after": "location_name",
			}
		).insert(ignore_permissions=True)


def create_location(**kwargs) -> "frappe.model.document.Document":
	ensure_location_custom_field()
	doc = frappe.get_doc(
		{
			"doctype": "Location",
			"location_name": kwargs.pop("location_name", None) or f"_Test Location {frappe.generate_hash(length=6)}",
			# LOA.validate warns if a location has no code, so default one (pass
			# custom_location_code="" explicitly to test the missing-code path).
			"custom_location_code": kwargs.pop("custom_location_code", f"LC-{frappe.generate_hash(length=4)}"),
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


# --------------------------------------------------------------------------
# Vehicle Movement (period-based rental)
# --------------------------------------------------------------------------
def create_vehicle_movement(do_not_submit: bool = False, **kwargs) -> "frappe.model.document.Document":
	"""Create a Vehicle Movement (rental). Defaults to a Without-Driver rental of a
	freshly-created Idle vehicle to a freshly-created customer/project.

	Pass `vehicle=`, `customer=`, `project_to=`, `movement_date=`, `rent_type=`,
	`driver_shifts=[{driver, shift}, ...]` to override.
	"""
	vehicle = kwargs.pop("vehicle", None) or create_vehicle().name
	customer = kwargs.pop("customer", None) or create_customer().name
	project = kwargs.pop("project_to", None) or create_project(customer=customer).name
	values = {
		"doctype": "Vehicle Movement",
		"vehicle": vehicle,
		"customer": customer,
		"project_to": project,
		"movement_date": kwargs.pop("movement_date", nowdate()),
		"invoiceable": kwargs.pop("invoiceable", 1),
	}
	values.update(kwargs)  # driver=, invoiceable=, demobilize_date=, …
	doc = frappe.get_doc(values)
	doc.insert(ignore_permissions=True)
	if not do_not_submit:
		doc.submit()
	return doc


def create_vehicle_no_plate_code(**kwargs) -> "frappe.model.document.Document":
	"""A Vehicle missing the now-mandatory custom_plate_code / custom_ownership_status,
	mirroring the 359 live vehicles. Inserted with ignore_mandatory so tracking-state
	updates (which must use db.set_value) can be regression-tested."""
	ensure_uom("Nos")
	doc = frappe.get_doc(
		{
			"doctype": "Vehicle",
			"license_plate": kwargs.pop("license_plate", None) or f"_TNP-{frappe.generate_hash(length=8)}",
			"make": "_Test Make",
			"model": "_Test Model",
			"last_odometer": 0,
			"fuel_type": "Petrol",
			"uom": "Nos",
			**kwargs,
		}
	)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return doc


# --------------------------------------------------------------------------
# Monthly Billing
# --------------------------------------------------------------------------
def create_monthly_billing(customer, billing_month, do_not_submit: bool = False, **kwargs):
	"""Create + build a Monthly Billing sheet for a customer/month (submitted by
	default). Returns the document."""
	doc = frappe.get_doc(
		{
			"doctype": "Monthly Billing",
			"customer": customer,
			"billing_month": billing_month,
			**kwargs,
		}
	)
	doc.build()
	doc.insert(ignore_permissions=True)
	if not do_not_submit:
		doc.submit()
	return doc
