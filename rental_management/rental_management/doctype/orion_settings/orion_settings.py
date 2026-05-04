# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OrionSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.role_details.role_details import RoleDetails
		from rental_management.rental_management.doctype.ticket_entitlement.ticket_entitlement import TicketEntitlement

		company_logo: DF.AttachImage | None
		default_bank_name_for_c3_pay: DF.Data | None
		manual_paid_check_read_only_date: DF.Date | None
		role_for_non_office_employee_ssa_access: DF.TableMultiSelect[RoleDetails]
		ss_print_logo: DF.AttachImage | None
		ticket_entitlement_detail: DF.Table[TicketEntitlement]
	# end: auto-generated types
	pass
