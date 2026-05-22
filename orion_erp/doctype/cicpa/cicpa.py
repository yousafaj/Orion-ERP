import frappe
from frappe import _
from frappe.model.document import Document

class CICPA(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		active: DF.Check
		amended_from: DF.Link | None
		cicpa_status: DF.Literal["", "Active", "Cancelled", "Expired"]
		cicpa_type: DF.Literal["", "Driver", "Vehicle"]
		document: DF.Attach | None
		driver: DF.Link | None
		expiry_date: DF.Date
		issue_date: DF.Date
		loa: DF.Link
		vehicle: DF.Link | None
	# end: auto-generated types
 
	def validate(self):
		if not self.loa or not self.cicpa_type:
			return

		loa_doc = frappe.get_doc("LOA", self.loa)

		if self.cicpa_type == "Vehicle":
			if loa_doc.remaining_vehicle_quota <= 0 or loa_doc.total_created_vehicle_cicpa >= loa_doc.total_vehicle_quota:
				frappe.throw(_("Cannot create CICPA: Vehicle quota exhausted or invalid in LOA {0}.").format(loa_doc.name))

		elif self.cicpa_type == "Driver":
			if loa_doc.remaining_driver_quota <= 0 or loa_doc.total_created_driver_cicpa >= loa_doc.total_driver_quota:
				frappe.throw(_("Cannot create CICPA: Driver quota exhausted or invalid in LOA {0}.").format(loa_doc.name))

		
	def on_submit(self):
		if self.loa:
			try:
				loa_doc = frappe.get_doc("LOA", self.loa)

				if self.cicpa_type == "Vehicle":
					loa_doc.total_created_vehicle_cicpa = (loa_doc.total_created_vehicle_cicpa or 0) + 1

				elif self.cicpa_type == "Driver":
					loa_doc.total_created_driver_cicpa = (loa_doc.total_created_driver_cicpa or 0) + 1

				loa_doc.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "Error updating LOA CICPA count on submit")
				frappe.throw(_("Failed to update LOA record: {0}").format(str(e)))

	def on_trash(self):
		if self.loa:
			try:
				loa_doc = frappe.get_doc("LOA", self.loa)

				if self.cicpa_type == "Vehicle" and loa_doc.total_created_vehicle_cicpa:
					loa_doc.total_created_vehicle_cicpa = max(0, (loa_doc.total_created_vehicle_cicpa or 0) - 1)

				elif self.cicpa_type == "Driver" and loa_doc.total_created_driver_cicpa:
					loa_doc.total_created_driver_cicpa = max(0, (loa_doc.total_created_driver_cicpa or 0) - 1)

				loa_doc.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "Error updating LOA CICPA count on delete")
				frappe.throw(_("Failed to update LOA record during deletion: {0}").format(str(e)))

	def on_change(self):
		# --- Update Vehicle Certification if cicpa_type is Vehicle ---
		if self.cicpa_type == "Vehicle" and self.vehicle:
			try:
				vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
				updated = False

				for row in vehicle_doc.get("custom_vehicle_certifications", []):
					if row.certification_name == "CICPA" and row.reference_no == self.name:
						row.date_of_expiry = self.expiry_date
						updated = True
						break

				if updated:
					vehicle_doc.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "Error updating CICPA expiry date in Vehicle")
				frappe.throw(_("Failed to update CICPA expiry date in Vehicle: {0}").format(str(e)))

		# --- Update Driver Certification if cicpa_type is Driver ---
		if self.cicpa_type == "Driver" and self.driver:
			try:
				driver_doc = frappe.get_doc("Driver", self.driver)
				updated = False

				for row in driver_doc.get("custom_certification_list", []):
					if row.certification_name == "CICPA" and row.reference_no == self.name:
						row.date_of_expiry = self.expiry_date
						updated = True
						break

				if updated:
					driver_doc.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "Error updating CICPA expiry date in Driver")
				frappe.throw(_("Failed to update CICPA expiry date in Driver: {0}").format(str(e)))

	def before_cancel(self):

		if self.loa:
			self.db_set("loa", None, update_modified=False)

		try:
			cicpa_logs = frappe.get_all(
				"CICPA Logs",
				filters={"cicpa": self.name},
				fields=["name", "docstatus"]
			)

			for log in cicpa_logs:
				frappe.db.set_value(
					"CICPA Logs",
					log.name,
					"cicpa",
					None
				)

				log_doc = frappe.get_doc("CICPA Logs", log.name)
				if log_doc.docstatus == 1:
					log_doc.cancel()

				log_doc.delete(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				"CICPA before_cancel: CICPA Logs cleanup failed"
			)
			frappe.throw(
				_("Cannot cancel CICPA due to linked CICPA Logs: {0}")
				.format(str(e))
			)

		if self.cicpa_type == "Vehicle" and self.vehicle:
			try:
				vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)

				vehicle_doc.custom_has_cicpa = 0
				vehicle_doc.custom_cicpa = None

				vehicle_doc.custom_vehicle_certifications = [
					row for row in vehicle_doc.get("custom_vehicle_certifications", [])
					if not (
						row.certification_name == "CICPA"
						and row.reference_no == self.name
					)
				]

				vehicle_doc.save(ignore_permissions=True)
				if self.vehicle:
					self.db_set("vehicle", None, update_modified=False)

			except Exception as e:
				frappe.log_error(
					frappe.get_traceback(),
					"CICPA before_cancel: Vehicle cleanup failed"
				)
				frappe.throw(
					_("Failed to clean CICPA from Vehicle: {0}").format(str(e))
				)

		if self.cicpa_type == "Driver" and self.driver:
			try:
				driver_doc = frappe.get_doc("Driver", self.driver)

				driver_doc.custom_has_cicpa = 0
				driver_doc.custom_cicpa = None

				driver_doc.custom_certification_list = [
					row for row in driver_doc.get("custom_certification_list", [])
					if not (
						row.certification_name == "CICPA"
						and row.reference_no == self.name
					)
				]

				driver_doc.save(ignore_permissions=True)
				if self.driver:
					self.db_set("driver", None, update_modified=False)

			except Exception as e:
				frappe.log_error(
					frappe.get_traceback(),
					"CICPA before_cancel: Driver cleanup failed"
				)
				frappe.throw(
					_("Failed to clean CICPA from Driver: {0}").format(str(e))
				)