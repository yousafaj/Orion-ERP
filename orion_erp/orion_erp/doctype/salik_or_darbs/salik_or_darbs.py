# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from orion_erp.orion_erp.services.salik import (
    norm_plate as _norm_plate,
    parse_date as _parse_date,
    clean_amount as _clean_amount,
    cell as _cell,
    build_plate_index as _build_plate_index,
    import_salik,
    download_template,
    parse_salik_statement as _parse_salik_statement,
)


class SalikorDarbs(Document):
    def autoname(self):
        from frappe.utils import get_first_day, getdate
        self.billing_month = get_first_day(getdate(self.billing_month))
        self.name = f"SAL-{self.vehicle}-{self.billing_month}"

    def validate(self):
        from frappe.utils import get_first_day, getdate
        from frappe.utils import flt
        if self.billing_month:
            self.billing_month = get_first_day(getdate(self.billing_month))
        self.total_amount = sum(flt(r.amount) for r in (self.crossings or []))
