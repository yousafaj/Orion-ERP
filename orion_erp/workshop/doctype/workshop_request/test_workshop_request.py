import frappe
from frappe.tests.utils import FrappeTestCase

from orion_erp.tests.fixtures import create_vehicle, get_company


class TestWorkshopRequest(FrappeTestCase):
    def test_request_reuses_vehicle_master(self):
        vehicle = create_vehicle(custom_ownership_status="Rented")
        vehicle_count = frappe.db.count("Vehicle")
        request = frappe.get_doc(
            {
                "doctype": "Workshop Request",
                "company": get_company(),
                "vehicle": vehicle.name,
                "request_type": "Corrective",
                "priority": "Normal",
                "approval_category": "Ordinary",
                "complaint": "Test complaint",
            }
        ).insert(ignore_permissions=True)

        self.assertEqual(request.vehicle, vehicle.name)
        self.assertEqual(request.vehicle_ownership_status, "Rented")
        self.assertFalse(request.asset)
        self.assertEqual(frappe.db.count("Vehicle"), vehicle_count)

    def test_job_card_requires_approved_request(self):
        from orion_erp.workshop.doctype.workshop_request.workshop_request import make_job_card

        request = frappe.get_doc(
            {
                "doctype": "Workshop Request",
                "company": get_company(),
                "vehicle": create_vehicle().name,
                "complaint": "Test complaint",
            }
        ).insert(ignore_permissions=True)
        with self.assertRaises(frappe.ValidationError):
            make_job_card(request.name)
