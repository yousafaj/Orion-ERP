# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class LEAVEDECLARATION(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		company: DF.Link
		data: DF.Data
		designation: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		leave_days: DF.Float
		leave_end_date: DF.Date | None
		leave_start_date: DF.Date
		leaving_date: DF.Date
		passport_number: DF.Data
	# end: auto-generated types
	pass

import frappe

@frappe.whitelist()
def get_passport_number(employee):
    """
    Fetch the Passport Number of an employee from the Custom Certificates child table.
    Args:
        employee (str): Employee ID selected in the LEAVE DECLARATION form.

    Returns:
        str | None: Passport number (reference_no) if found, otherwise None.
    """

    # Fetch reference_no from Custom Certificates child table
    passport = frappe.db.get_value(
        "Employee cdt",
        {
            "parent": employee,
            "certification_name": "Passport no"
        },
        "reference_no"
    )

    # Return the fetched passport number
    return passport