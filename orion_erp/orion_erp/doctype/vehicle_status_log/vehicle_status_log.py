# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, today


class VehicleStatusLog(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        days: DF.Int
        from_date: DF.Date | None
        parent: DF.Data
        parentfield: DF.Data
        parenttype: DF.Data
        reason: DF.SmallText | None
        source_order: DF.Link | None
        status: DF.Literal["Idle", "Workshop"]
        to_date: DF.Date | None
        vehicle: DF.Link
        workshop_name: DF.Data | None
    # end: auto-generated types
    def validate(self):
        if self.to_date and self.from_date and self.to_date < self.from_date:
            frappe.throw("To Date cannot be before From Date.")
        self.days = date_diff(self.to_date or today(), self.from_date)