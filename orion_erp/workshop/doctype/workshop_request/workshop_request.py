import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


APPROVAL_STATUSES = {"Approved", "Rejected"}
MANAGER_ONLY_CATEGORIES = {"Major", "Exception"}


class WorkshopRequest(Document):
    def before_validate(self):
        self.requested_on = self.requested_on or now_datetime()
        self._set_vehicle_details()

    def validate(self):
        self._validate_asset_link()
        self._validate_approval_authority()
        self._validate_job_card_state()

    def _set_vehicle_details(self):
        if not self.vehicle:
            return
        vehicle = frappe.db.get_value(
            "Vehicle",
            self.vehicle,
            ["custom_company", "custom_ownership_status", "custom_asset_mapping"],
            as_dict=True,
        )
        if not vehicle:
            return
        self.company = self.company or vehicle.custom_company
        self.vehicle_ownership_status = vehicle.custom_ownership_status
        self.asset = self.asset or vehicle.custom_asset_mapping

    def _validate_asset_link(self):
        if not self.vehicle or not self.asset:
            return
        mapped_asset = frappe.db.get_value("Vehicle", self.vehicle, "custom_asset_mapping")
        if mapped_asset and mapped_asset != self.asset:
            frappe.throw(
                _("Asset {0} is not mapped to Vehicle {1}.").format(self.asset, self.vehicle)
            )

    def _validate_approval_authority(self):
        previous = self.get_doc_before_save()
        previous_status = previous.status if previous else None
        if self.status not in APPROVAL_STATUSES or self.status == previous_status:
            return

        roles = set(frappe.get_roles())
        manager_roles = {"Workshop Manager", "System Manager"}
        supervisor_roles = manager_roles | {"Workshop Supervisor"}
        allowed_roles = manager_roles if self.approval_category in MANAGER_ONLY_CATEGORIES else supervisor_roles
        if not roles.intersection(allowed_roles):
            frappe.throw(_("You are not authorized to approve or reject this Workshop Request."), frappe.PermissionError)

    def _validate_job_card_state(self):
        if self.status == "Job Card Created" and not self.job_card:
            frappe.throw(_("A Job Card reference is required for status Job Card Created."))


@frappe.whitelist()
def make_job_card(request_name):
    request = frappe.get_doc("Workshop Request", request_name)
    request.check_permission("write")
    if request.status != "Approved":
        frappe.throw(_("Approve the Workshop Request before creating a Job Card."))
    if request.job_card:
        return request.job_card

    job = frappe.get_doc(
        {
            "doctype": "Workshop Job Card",
            "workshop_request": request.name,
            "company": request.company,
            "vehicle": request.vehicle,
            "asset": request.asset,
            "odometer_in": request.odometer,
            "check_in": now_datetime(),
            "status": "Inspection",
        }
    )
    job.insert()
    request.db_set("job_card", job.name, update_modified=False)
    request.db_set("status", "Job Card Created", update_modified=True)
    return job.name
