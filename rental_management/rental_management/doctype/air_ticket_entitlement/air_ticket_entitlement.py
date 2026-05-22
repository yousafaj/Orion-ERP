# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AirTicketEntitlement(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		employee: DF.Link
		employee_onboarding_date: DF.Date | None
		status: DF.Literal["", "Pending", "Paid"]
		ticket_amount: DF.Currency
		ticket_entitlement_duration: DF.Data | None
	# end: auto-generated types
	pass
