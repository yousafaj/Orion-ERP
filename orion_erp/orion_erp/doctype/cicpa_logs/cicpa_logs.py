# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CICPALogs(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		cicpa: DF.Data | None
		driver: DF.Link | None
		loa: DF.Link | None
		remarks: DF.Text | None
		vehicle: DF.Link | None
	# end: auto-generated types
	pass


	def on_update(self):
		"""
		If CICPA is removed (set to NULL),
		auto-cancel and delete this log
		"""

		# If cicpa is empty → cleanup this log
		if not self.cicpa:

			if frappe.flags.in_cicpa_log_cleanup:
				return

			frappe.flags.in_cicpa_log_cleanup = True

			try:
				doc = frappe.get_doc(self.doctype, self.name)
				if doc.docstatus == 1:
					doc.cancel()
				doc.delete(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(
					frappe.get_traceback(),
					"CICPA Logs auto cleanup failed"
				)
				frappe.throw(
					_("Failed to auto-delete CICPA Log: {0}")
					.format(str(e))
				)