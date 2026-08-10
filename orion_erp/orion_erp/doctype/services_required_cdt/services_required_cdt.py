# Copyright (c) 2026, mahak and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ServicesRequiredcdt(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		quotation_type: DF.Link | None
	# end: auto-generated types
	pass
