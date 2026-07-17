# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, flt


class LEAVEDECLARATION(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from orion_erp.orion_erp.doctype.leave_declaration_asset_clearance_detail.leave_declaration_asset_clearance_detail import LeaveDeclarationAssetClearanceDetail
		from orion_erp.orion_erp.doctype.access_card_detail.access_card_detail import AccessCardDetail
		from orion_erp.orion_erp.doctype.leave_declaration_salary_detail.leave_declaration_salary_detail import LeaveDeclarationSalaryDetail

		accommodation_clearances: DF.Data | None
		access_card_detail: DF.Table[AccessCardDetail]
		amended_from: DF.Link | None
		asset_clearance_detail: DF.Table[LeaveDeclarationAssetClearanceDetail]
		company: DF.Link
		data: DF.Data
		designation: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		leave_application: DF.Link
		leave_days: DF.Float
		leave_end_date: DF.Date | None
		leave_start_date: DF.Date
		leave_type: DF.Link
		leave_balance_before: DF.Float
		leaving_date: DF.Date
		outstanding_advance: DF.Currency
		passport_number: DF.Data
		rejoining_date: DF.Date | None
		remark: DF.SmallText | None
		salary_detail: DF.Table[LeaveDeclarationSalaryDetail]
		uniform: DF.Data | None
		vehicle_fine: DF.Currency
		vehicle_handover: DF.Data | None
	# end: auto-generated types

	def validate(self):
		if self.leave_application:
			self._validate_leave_application_not_used()
			self._validate_leave_type_not_unpaid()
			self._fetch_data_from_leave_application()
		self._fetch_outstanding_advance()

	def on_submit(self):
		if self.leave_application:
			frappe.db.set_value(
				"Leave Application",
				self.leave_application,
				"custom_leave_declaration",
				self.name,
			)
		self._update_asset_status_on_submit()

	def on_cancel(self):
		if self.leave_start_date and getdate(self.leave_start_date) <= getdate():
			frappe.throw(
				_("Cannot cancel Leave Declaration after the leave start date has passed.")
			)
		if self.leave_application:
			frappe.db.set_value(
				"Leave Application",
				self.leave_application,
				"custom_leave_declaration",
				None,
			)
		self._update_asset_status_on_cancel()

	def _validate_leave_application_not_used(self):
		existing = frappe.db.get_value(
			"Leave Declaration",
			{
				"leave_application": self.leave_application,
				"docstatus": 1,
				"name": ["!=", self.name],
			},
			"name",
		)
		if existing:
			frappe.throw(
				_("Leave Application {0} is already linked to Leave Declaration {1}.")
				.format(frappe.bold(self.leave_application), frappe.bold(existing))
			)

		la_declaration = frappe.db.get_value(
			"Leave Application",
			self.leave_application,
			"custom_leave_declaration",
		)
		if la_declaration and la_declaration != self.name:
			frappe.throw(
				_("Leave Application {0} is already linked to Leave Declaration {1}.")
				.format(frappe.bold(self.leave_application), frappe.bold(la_declaration))
			)

	def _validate_leave_type_not_unpaid(self):
		if self.leave_type:
			is_lwp = frappe.db.get_value("Leave Type", self.leave_type, "is_lwp")
			if is_lwp:
				frappe.throw(
					_("Leave Declaration is not applicable for Unpaid Leave types.")
				)

	def _fetch_data_from_leave_application(self):
		la = frappe.get_doc("Leave Application", self.leave_application)
		self.employee = la.employee
		self.employee_name = la.employee_name
		self.company = la.company
		self.leave_type = la.leave_type
		self.leave_start_date = la.from_date
		self.leave_end_date = la.to_date
		self.leaving_date = la.from_date

		emp = frappe.get_cached_doc("Employee", self.employee)
		self.designation = emp.designation
		self.passport_number = self._get_passport_number(self.employee)

		if not self.asset_clearance_detail:
			self._fetch_asset_details()

	def _fetch_asset_details(self):
		self.asset_clearance_detail = []
		if not self.employee:
			return

		assets = _get_employee_active_assets(self.employee)
		for asset in assets:
			row = self.append("asset_clearance_detail", {})
			row.asset_type = asset.get("asset_type")
			row.asset_code = asset.get("asset_code")
			row.issued_by = asset.get("issued_by")
			row.issued_date = asset.get("issued_date")
			row.attachment_upload = asset.get("attachment_upload")
			row.asset_status = asset.get("asset_status")
			row.qty = asset.get("qty")
			row.return_date = asset.get("return_date")
			row.remarks = asset.get("remarks")
			row.sim_card_number = asset.get("sim_card_number")
			row.network = asset.get("network")
			row.sim_status = asset.get("sim_status")
			row.brand = asset.get("brand")
			row.model = asset.get("model")
			row.imei_number = asset.get("imei_number")
			row.sim_number = asset.get("sim_number")
			row.network_provider = asset.get("network_provider")
			row.condition = asset.get("condition")
			row.vehicle_type = asset.get("vehicle_type")
			row.brand_model = asset.get("brand_model")
			row.plate_number = asset.get("plate_number")
			row.vehicle_cicpa_pass = asset.get("vehicle_cicpa_pass")
			row.fuel_type = asset.get("fuel_type")
			row.mulkiya_expiry_uae_specific = asset.get("mulkiya_expiry_uae_specific")
			row.odometer_reading_at_issue = asset.get("odometer_reading_at_issue")
			row.odometer_reading_at_return = asset.get("odometer_reading_at_return")
			row.name_of_last_user = asset.get("name_of_last_user")
			row.device_type = asset.get("device_type")
			row.it_brand = asset.get("it_brand")
			row.it_model = asset.get("it_model")
			row.attachment = asset.get("attachment")
			row.card_number = asset.get("card_number")
			row.card_issue_date = asset.get("card_issue_date")
			row.lost__reissued = asset.get("lost__reissued")
			row.pass_number = asset.get("pass_number")
			row.valid_to = asset.get("valid_to")
			row.cicpa_status = asset.get("cicpa_status")
			row.linked_account = asset.get("linked_account")
			row.expiry_date = asset.get("expiry_date")
			row.request_date = asset.get("request_date")
			row.parking_status = asset.get("parking_status")
			row.parking_slot_number = asset.get("parking_slot_number")
			row.source_asset_handover = asset.get("parent")
			row.source_asset_handover_detail = asset.get("name")

	def _fetch_outstanding_advance(self):
		if not self.employee:
			return
		self.outstanding_advance = _get_employee_outstanding_deductions(self.employee)

	def _update_asset_status_on_submit(self):
		if not self.asset_clearance_detail:
			return

		for row in self.asset_clearance_detail:
			if not row.source_asset_handover_detail:
				continue

			current_status = frappe.db.get_value(
				"Asset Handover Detail", row.source_asset_handover_detail, "asset_status"
			)

			target_status = row.asset_status
			if not target_status:
				continue

			if not row.previous_asset_status:
				row.previous_asset_status = current_status
			frappe.db.set_value(
				"Leave Declaration Asset Clearance Detail",
				row.name,
				"previous_asset_status",
				current_status,
			)

			if target_status == current_status:
				continue

			update_fields = {"asset_status": target_status}
			if target_status in ("Returned", "Lost", "Damaged"):
				update_fields["return_date"] = row.return_date or getdate()
			else:
				update_fields["return_date"] = None

			frappe.db.set_value(
				"Asset Handover Detail",
				row.source_asset_handover_detail,
				update_fields,
			)

		frappe.db.commit()

	def _update_asset_status_on_cancel(self):
		if not self.asset_clearance_detail:
			return

		for row in self.asset_clearance_detail:
			if not row.source_asset_handover_detail:
				continue

			previous_status = row.previous_asset_status
			if not previous_status:
				continue

			current_status = frappe.db.get_value(
				"Asset Handover Detail", row.source_asset_handover_detail, "asset_status"
			)
			if current_status == previous_status:
				continue

			update_fields = {"asset_status": previous_status}

			frappe.db.set_value(
				"Asset Handover Detail",
				row.source_asset_handover_detail,
				update_fields,
			)

	@staticmethod
	def _get_passport_number(employee):
		passport = frappe.db.get_value(
			"Employee cdt",
			{
				"parent": employee,
				"certification_name": "Passport no",
			},
			"reference_no",
		)
		return passport


@frappe.whitelist()
def get_leave_balance(employee, leave_type, date):
	from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
	return get_leave_balance_on(employee, leave_type, date)


def _get_employee_active_assets(employee):
	return frappe.db.sql(
		"""
		SELECT ahd.*
		FROM `tabAsset Handover Detail` ahd
		INNER JOIN `tabAsset Handover` ah ON ah.name = ahd.parent
		WHERE ah.employee = %s
		ORDER BY ah.creation DESC
		""",
		employee,
		as_dict=True,
	)


@frappe.whitelist()
def get_employee_asset_details(employee):
	return _get_employee_active_assets(employee)


@frappe.whitelist()
def get_leave_application_data(leave_application):
	la = frappe.get_doc("Leave Application", leave_application)
	emp = frappe.get_cached_doc("Employee", la.employee)
	passport = frappe.db.get_value(
		"Employee cdt",
		{
			"parent": la.employee,
			"certification_name": "Passport no",
		},
		"reference_no",
	)

	return {
		"employee": la.employee,
		"employee_name": la.employee_name,
		"company": la.company,
		"leave_type": la.leave_type,
		"leave_start_date": la.from_date,
		"leave_end_date": la.to_date,
		"leaving_date": la.from_date,
		"designation": emp.designation,
		"passport_number": passport,
	}


@frappe.whitelist()
def get_available_leave_applications(doctype, txt, searchfield, start, page_length, filters):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)

	filters = filters or {}
	employee = filters.get("employee")

	unpaid_types = frappe.get_all("Leave Type", filters={"is_lwp": 1}, pluck="name")

	from frappe.query_builder import DocType

	LA = DocType("Leave Application")

	query = (
		frappe.qb.from_(LA)
		.select(LA.name, LA.employee_name, LA.leave_type, LA.from_date, LA.to_date)
		.where(LA.docstatus == 1)
		.where(LA.custom_approval_status == "Approved")
		.where(LA.custom_leave_declaration.isnull())
		.orderby(LA.from_date, order=frappe.qb.desc)
	)

	if unpaid_types:
		query = query.where(LA.leave_type.notin(unpaid_types))
	if employee:
		query = query.where(LA.employee == employee)
	if txt:
		search_term = f"%{txt}%"
		query = query.where(
			(LA.name.like(search_term))
			| (LA.employee_name.like(search_term))
			| (LA.leave_type.like(search_term))
		)

	apps = query.run(as_dict=True)
	return [[a.name, a.employee_name or "", a.leave_type or "", str(a.from_date) if a.from_date else "", str(a.to_date) if a.to_date else ""] for a in apps]


@frappe.whitelist()
def get_passport_number(employee):
	passport = frappe.db.get_value(
		"Employee cdt",
		{
			"parent": employee,
			"certification_name": "Passport no",
		},
		"reference_no",
	)
	return passport


def _get_employee_outstanding_deductions(employee):
	total = 0

	latest_deduction = frappe.get_all(
		"Employee Deduction",
		filters={"employee": employee, "docstatus": 1},
		fields=["name"],
		order_by="creation desc",
		limit=1,
	)

	if not latest_deduction:
		return total

	ed = frappe.get_doc("Employee Deduction", latest_deduction[0].name)

	for row in ed.employee_deduction_detail or []:
		deduction = flt(row.deduction_amount) or 0
		paid = flt(row.paid_amount) or 0
		remaining = deduction - paid
		if remaining > 0:
			total += remaining

	for row in ed.outstanding_employee_deduction_detail or []:
		deduction = flt(row.deduction_amount) or 0
		paid = flt(row.paid_amount) or 0
		remaining = deduction - paid
		if remaining > 0:
			total += remaining

	return total


@frappe.whitelist()
def get_outstanding_advance(employee):
	return _get_employee_outstanding_deductions(employee)
