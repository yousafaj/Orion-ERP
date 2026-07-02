# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate


class LEAVEDECLARATION(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		company: DF.Link
		created_leave_application: DF.Data | None
		data: DF.Data
		designation: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		extended_leave_application: DF.Data | None
		leave_days: DF.Float
		leave_end_date: DF.Date | None
		leave_start_date: DF.Date
		leave_type: DF.Link
		leaving_date: DF.Date
		passport_number: DF.Data
		rejoining_date: DF.Date | None
	# end: auto-generated types

	def on_submit(self):
		existing_leave = self._get_existing_leave_application()

		if self.rejoining_date:
			rj_date = getdate(self.rejoining_date)
			# rejoining_date is first day back at work, last leave day is rj_date - 1
			last_leave_day = add_days(rj_date, -1)

			if rj_date <= getdate(self.leave_end_date):
				# Early return or same-day return: adjust leave end
				if not existing_leave:
					if getdate(self.leave_start_date) <= last_leave_day:
						self._create_leave_application(self.leave_start_date, last_leave_day)
						self.db_set("created_leave_application", self._created_la_name)
						frappe.msgprint(
							_("Leave application {0} created for employee {1}.").format(
								frappe.bold(self._created_la_name), frappe.bold(self.employee_name)
							),
							title=_("Leave Application Created")
						)
				else:
					self._handle_early_rejoining(existing_leave)
			else:
				# Late return: create base LA for original period; extension handled by Rejoining Form
				if not existing_leave:
					self._create_leave_application(self.leave_start_date, self.leave_end_date)
					self.db_set("created_leave_application", self._created_la_name)
					frappe.msgprint(
						_("Leave application {0} created for employee {1}. Extended leave will be created on rejoining.").format(
							frappe.bold(self._created_la_name), frappe.bold(self.employee_name)
						),
						title=_("Leave Application Created"),
						indicator="green"
					)
			return

		if not existing_leave:
			self._create_leave_application(self.leave_start_date, self.leave_end_date)
			self.db_set("created_leave_application", self._created_la_name)
			frappe.msgprint(
				_("Leave application {0} created for employee {1}. Kindly approve to impact the leaves.").format(
					frappe.bold(self._created_la_name), frappe.bold(self.employee_name)
				),
				title=_("Leave Application Created"),
				indicator="green"
			)

	def on_cancel(self):
		if self.created_leave_application:
			self._cancel_leave_application(self.created_leave_application)
		if self.extended_leave_application:
			self._cancel_leave_application(self.extended_leave_application)

	def _get_existing_leave_application(self):
		applications = frappe.get_all(
			"Leave Application",
			filters={
				"employee": self.employee,
				"from_date": ["<=", self.leave_end_date],
				"to_date": [">=", self.leave_start_date],
				"docstatus": ["!=", 2],
				"leave_type": self.leave_type
			},
			fields=["name", "from_date", "to_date"],
			limit=1
		)
		return applications[0] if applications else None

	def _create_leave_application(self, from_date, to_date):
		la = frappe.new_doc("Leave Application")
		la.employee = self.employee
		la.employee_name = self.employee_name
		la.leave_type = self.leave_type
		la.from_date = from_date
		la.to_date = to_date
		la.company = self.company
		la.description = _("Auto-created from Leave Declaration {0}").format(self.name)
		la.status = "Open"
		la.custom_approval_status = "Open"

		emp = frappe.get_cached_doc("Employee", self.employee)
		la.leave_approver = emp.leave_approver
		la.custom_leave_approver_1 = emp.get("custom_leave_approver_1")
		la.custom_leave_approver_2 = emp.get("custom_leave_approver_2")
		la.custom_leave_approver_4 = emp.get("custom_leave_approver_3")
		la.custom_leave_approver_5 = emp.get("custom_leave_approver_4")
		la.custom_employee_user_id = emp.user_id

		la.flags.ignore_permissions = True
		la.insert()
		self._created_la_name = la.name

	def _handle_early_rejoining(self, existing_leave):
		rj_date = getdate(self.rejoining_date)
		self._cancel_leave_application(existing_leave["name"])
		last_leave_day = add_days(rj_date, -1)
		if getdate(self.leave_start_date) <= last_leave_day:
			self._create_leave_application(self.leave_start_date, last_leave_day)
			self.db_set("created_leave_application", self._created_la_name)
			frappe.msgprint(
				_("Employee returned early. Previous leave application {0} cancelled and new application {1} created with correct dates.").format(
					frappe.bold(existing_leave["name"]), frappe.bold(self._created_la_name)
				),
				title=_("Leave Application Adjusted"),
				indicator="orange"
			)
		else:
			frappe.msgprint(
				_("Employee returned early. Previous leave application {0} cancelled.").format(
					frappe.bold(existing_leave["name"])
				),
				title=_("Leave Application Cancelled"),
				indicator="orange"
			)

	@staticmethod
	def _cancel_leave_application(la_name):
		la = frappe.get_doc("Leave Application", la_name)
		if la.docstatus == 0:
			la.flags.ignore_permissions = True
			la.db_set("docstatus", 2)
		elif la.docstatus == 1:
			la.flags.ignore_permissions = True
			la.cancel()


@frappe.whitelist()
def get_passport_number(employee):
    passport = frappe.db.get_value(
        "Employee cdt",
        {
            "parent": employee,
            "certification_name": "Passport no"
        },
        "reference_no"
    )
    return passport
