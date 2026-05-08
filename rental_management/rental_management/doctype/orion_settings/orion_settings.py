# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class OrionSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.role_details.role_details import RoleDetails
		from rental_management.rental_management.doctype.ticket_entitlement.ticket_entitlement import TicketEntitlement

		company_logo: DF.AttachImage | None
		cron_schedule_date_noe: DF.Date | None
		cron_schedule_date_oe: DF.Date | None
		default_bank_name_for_c3_pay: DF.Data | None
		last_month_for_which_payment_processed_noe: DF.Date | None
		last_month_for_which_payment_processed_oe: DF.Date | None
		manual_paid_check_read_only_date: DF.Date | None
		payroll_month_date_noe: DF.Date | None
		payroll_month_date_oe: DF.Date | None
		role_for_non_office_employee_ssa_access: DF.TableMultiSelect[RoleDetails]
		ss_print_logo: DF.AttachImage | None
		ticket_entitlement_detail: DF.Table[TicketEntitlement]
	# end: auto-generated types
	pass

	def validate(self):

		today = getdate()

		# ---------- OFFICE ----------
		if self.has_value_changed("payroll_month_date_oe"):
			if self.payroll_month_date_oe:

				payroll_date = getdate(self.payroll_month_date_oe)
				last_processed = getdate(self.last_month_for_which_payment_processed_oe) if self.last_month_for_which_payment_processed_oe else None

				if last_processed and payroll_date <= last_processed:
					frappe.throw("Payroll Month Date Office Employee must be greater than Last Processed Month")

				if payroll_date > today:
					frappe.throw("Payroll Month Date Office Employee cannot be greater than today")

		if self.has_value_changed("cron_schedule_date_oe"):
			if self.cron_schedule_date_oe:

				payroll_date = getdate(self.payroll_month_date_oe)
				cron_date = getdate(self.cron_schedule_date_oe)
				last_processed = getdate(self.last_month_for_which_payment_processed_oe) if self.last_month_for_which_payment_processed_oe else None

				if last_processed and cron_date <= last_processed:
					frappe.throw("Cron Schedule Date Office Employee must be greater than Last Processed Month")

				if last_processed and payroll_date <= last_processed:
					frappe.throw("Payroll Month Date Office Employee must be greater than Last Processed Month")
				if "Administrator" not in frappe.get_roles():
					if cron_date <= today:
						frappe.throw("Cron Schedule Date Office Employee must be greater than today")

		# ---------- NON OFFICE ----------
		if self.has_value_changed("payroll_month_date_noe"):
			if self.payroll_month_date_noe:

				payroll_date = getdate(self.payroll_month_date_noe)
				last_processed = getdate(self.last_month_for_which_payment_processed_noe) if self.last_month_for_which_payment_processed_noe else None

				if last_processed and payroll_date <= last_processed:
					frappe.throw("Payroll Month Date Non-Office Employee must be greater than Last Processed Month")

				if payroll_date > today:
					frappe.throw("Payroll Month Date Non-Office cannot be greater than today")

		if self.has_value_changed("cron_schedule_date_noe"):
			if self.cron_schedule_date_noe:

				payroll_date = getdate(self.payroll_month_date_noe)
				cron_date = getdate(self.cron_schedule_date_noe)
				last_processed = getdate(self.last_month_for_which_payment_processed_noe) if self.last_month_for_which_payment_processed_noe else None
				if last_processed and payroll_date <= last_processed:
					frappe.throw("Payroll Month Date Non-Office Employee must be greater than Last Processed Month")

				if last_processed and cron_date <= last_processed:
					frappe.throw("Cron Schedule Date Non-Office must be greater than Last Processed Month")

				if "Administrator" not in frappe.get_roles():
					if cron_date <= today:
						frappe.throw("Cron Schedule Date Non-Office must be greater than today")