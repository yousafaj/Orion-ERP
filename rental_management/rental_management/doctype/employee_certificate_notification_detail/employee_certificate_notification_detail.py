# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class EmployeeCertificateNotificationDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		certification_name: DF.Link | None
		condition: DF.Text | None
		field_notification_based_on: DF.Data | None
		message: DF.LongText | None
		notify_before_days: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		role: DF.Link | None
		sender: DF.Link | None
		sender_email: DF.Data | None
		subject: DF.Data | None
		trigger_email_to_employee: DF.Check
	# end: auto-generated types
	pass
