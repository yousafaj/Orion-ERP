# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class EmployeeCertificateNotificationSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.employee_certificate_notification_detail.employee_certificate_notification_detail import EmployeeCertificateNotificationDetail

		disable_notification: DF.Check
		employee_certificate_notification_detail: DF.Table[EmployeeCertificateNotificationDetail]
	# end: auto-generated types
	pass
