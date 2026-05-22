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
		cicpa_no: DF.Data | None
		cicpa_status: DF.Literal["", "Active", "Cancelled", "Lost", "Expired"]
		cicpa_type: DF.Literal["", "Driver", "Vehicle"]
		company: DF.Link | None
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
		# Keep the status field in sync and free the LOA quota, mirroring the
		# manual "Mark as Cancelled" flow. Only do this if the status is still
		# Active — if the user already transitioned the CICPA via mark_cicpa_status
		# the quota has already been freed, so skip to avoid double-counting.
		if self.cicpa_status == "Active":
			if self.loa:
				try:
					loa = frappe.get_doc("LOA", self.loa)
					if self.cicpa_type == "Vehicle":
						loa.total_created_vehicle_cicpa = max(0, (loa.total_created_vehicle_cicpa or 0) - 1)
						loa.remaining_vehicle_quota = (loa.remaining_vehicle_quota or 0) + 1
						loa.total_cancelled_vehicle_cicpa = (loa.total_cancelled_vehicle_cicpa or 0) + 1
					elif self.cicpa_type == "Driver":
						loa.total_created_driver_cicpa = max(0, (loa.total_created_driver_cicpa or 0) - 1)
						loa.remaining_driver_quota = (loa.remaining_driver_quota or 0) + 1
						loa.total_cancelled_driver_cicpa = (loa.total_cancelled_driver_cicpa or 0) + 1
					loa.save(ignore_permissions=True)
				except Exception:
					frappe.log_error(frappe.get_traceback(), "CICPA before_cancel: LOA quota update failed")
			self.db_set("cicpa_status", "Cancelled", update_modified=True)

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


@frappe.whitelist()
def mark_cicpa_status(cicpa, new_status):
	if new_status not in ("Cancelled", "Lost", "Expired"):
		frappe.throw(_("Invalid CICPA status."))

	doc = frappe.get_doc("CICPA", cicpa)
	if doc.docstatus != 1:
		frappe.throw(_("CICPA must be submitted before status can be changed."))
	if doc.cicpa_status != "Active":
		frappe.throw(_("CICPA status is already {0}.").format(doc.cicpa_status))

	doc.db_set("cicpa_status", new_status, update_modified=True)

	if doc.loa:
		loa = frappe.get_doc("LOA", doc.loa)
		if doc.cicpa_type == "Vehicle":
			loa.total_created_vehicle_cicpa = max(0, (loa.total_created_vehicle_cicpa or 0) - 1)
			loa.remaining_vehicle_quota = (loa.remaining_vehicle_quota or 0) + 1
			if new_status == "Cancelled":
				loa.total_cancelled_vehicle_cicpa = (loa.total_cancelled_vehicle_cicpa or 0) + 1
		elif doc.cicpa_type == "Driver":
			loa.total_created_driver_cicpa = max(0, (loa.total_created_driver_cicpa or 0) - 1)
			loa.remaining_driver_quota = (loa.remaining_driver_quota or 0) + 1
			if new_status == "Cancelled":
				loa.total_cancelled_driver_cicpa = (loa.total_cancelled_driver_cicpa or 0) + 1
		loa.save(ignore_permissions=True)


def auto_expire_cicpas():
	today = frappe.utils.nowdate()
	candidates = frappe.get_all(
		"CICPA",
		filters={"docstatus": 1, "cicpa_status": "Active", "expiry_date": ["<", today]},
		pluck="name",
	)
	for name in candidates:
		try:
			mark_cicpa_status(name, "Expired")
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"auto_expire_cicpas failed for {name}")