# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _ 
from frappe.model.document import Document


class TrafficFineorAccident(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.accident_logs.accident_logs import AccidentLogs
		from rental_management.rental_management.doctype.fines_cdt.fines_cdt import Finescdt

		accident_detail: DF.Table[AccidentLogs]
		amended_from: DF.Link | None
		closing_status: DF.Literal["", "Paid by Client", "Paid by Driver", "Paid by Company"]
		customer: DF.Link | None
		date: DF.Date
		detail: DF.Table[Finescdt]
		driver: DF.Link | None
		employment_type: DF.Link | None
		evidence: DF.Attach | None
		fine_status: DF.Literal["", "Faulty", "Not Faulty"]
		post_fine: DF.Check
		project: DF.Link | None
		shift: DF.Link | None
		status: DF.Literal["", "Open", "Closed"]
		vehicle: DF.Link | None
		vehicle_type: DF.Data | None
	# end: auto-generated types
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from rental_management.rental_management.doctype.accident_logs.accident_logs import AccidentLogs
		from rental_management.rental_management.doctype.fines_cdt.fines_cdt import Finescdt

		accident_detail: DF.Table[AccidentLogs]
		amended_from: DF.Link | None
		closing_status: DF.Literal["", "Paid by Client"]
		customer: DF.Link | None
		date: DF.Date
		detail: DF.Table[Finescdt]
		driver: DF.Link | None
		employment_type: DF.Link | None
		evidence: DF.Attach | None
		fine_status: DF.Literal["", "Faulty", "Not Faulty"]
		post_fine: DF.Check
		project: DF.Link | None
		shift: DF.Link | None
		vehicle: DF.Link | None
		vehicle_type: DF.Data | None
	# end: auto-generated type
 
	def on_submit(self):
		if not self.evidence:
			frappe.throw(_("You must attach Evidence before submitting this document."))
			return
		if not self.closing_status:
			frappe.throw(_("You must select a Closing Status before submitting this document."))
			return
		self.status = "Closed"

