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
		from orion_erp.doctype.role_details.role_details import RoleDetails
		from orion_erp.doctype.ticket_entitlement.ticket_entitlement import TicketEntitlement

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
		show_trigger_additional_deduction_non_office: DF.Check
		show_trigger_additional_deduction_office: DF.Check
		ss_print_logo: DF.AttachImage | None
		ticket_entitlement_detail: DF.Table[TicketEntitlement]
		vehicle_handover_image: DF.AttachImage | None
	# end: auto-generated types
	pass