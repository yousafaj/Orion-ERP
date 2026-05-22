# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExistingCertificates(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		certificate_name: DF.Data | None
		customer: DF.Link | None
		date_of_expiry: DF.Date | None
		date_of_issue: DF.Date | None
		driver: DF.Link | None
		employee: DF.Data | None
		mark_as_not_renew: DF.Check
		reference_no: DF.Data | None
		row_name: DF.Data | None
		vehicle: DF.Link | None
	# end: auto-generated types

	def validate(self):
		if not self.row_name or not self.date_of_expiry:
			return

		# Check if expiry date has changed
		if self.get_doc_before_save() and self.date_of_expiry != self.get_doc_before_save().date_of_expiry:
			parent_doc = None

			# Determine parent and child table
			if self.vehicle:
				parent_doc = frappe.get_doc("Vehicle", self.vehicle)
				child_table_field = "custom_vehicle_certifications"
			elif self.customer:
				parent_doc = frappe.get_doc("Customer", self.customer)
				child_table_field = "custom_customer_certificates"
			elif self.driver:
				parent_doc = frappe.get_doc("Driver", self.driver)
				child_table_field = "custom_driver_certifications"
			else:
				return

			if parent_doc and hasattr(parent_doc, child_table_field):
				updated = False
				for row in getattr(parent_doc, child_table_field):
					if row.name == self.row_name:
						row.date_of_expiry = self.date_of_expiry
						updated = True
						break
				if updated:
					parent_doc.save(ignore_permissions=True)

			if self.certificate_name == "CICPA" and self.reference_no:
				try:
					frappe.db.set_value("CICPA", self.reference_no, "expiry_date", self.date_of_expiry)
				except frappe.DoesNotExistError:
					frappe.throw(f"CICPA document '{self.reference_no}' not found.")