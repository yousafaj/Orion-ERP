# Copyright (c) 2026, Orion ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    add_months,
    date_diff,
    flt,
    get_first_day,
    get_last_day,
    getdate,
)


# ---------------------------------------------------------------------------
# Shared period helpers (also used by Salik plate→rental matching).
# ---------------------------------------------------------------------------
def period_covers(start, end, on_date) -> bool:
    """True if `on_date` falls within the rental period [start, end]. An open
    rental (end is falsy) is treated as ongoing — covers any date >= start."""
    on_date = getdate(on_date)
    if getdate(start) > on_date:
        return False
    return not end or getdate(end) >= on_date


def rental_on_date(vehicle, on_date):
    """The submitted Vehicle Movement whose rental period covers `on_date` for this
    vehicle (most recent first). Returns a dict with name/customer/project_to, or None.
    Shared by Salik matching and the fine/maintenance Customer auto-fill."""
    if not (vehicle and on_date):
        return None
    rentals = frappe.get_all(
        "Vehicle Movement",
        filters={"docstatus": 1, "vehicle": vehicle, "movement_date": ["<=", getdate(on_date)]},
        fields=["name", "customer", "project_to", "movement_date", "demobilize_date"],
        order_by="movement_date desc",
    )
    for r in rentals:
        if period_covers(r.movement_date, r.demobilize_date, on_date):
            return r
    return None


@frappe.whitelist()
def rental_customer(vehicle, on_date):
    """Client helper: the customer/project of the rental covering a date (for the
    fine / maintenance forms to auto-fill Customer)."""
    r = rental_on_date(vehicle, on_date)
    return {"customer": r.customer, "project": r.project_to} if r else {}


def billable_days(rental_start, rental_end, month_start, month_end) -> int:
    """Inclusive count of days the rental period overlaps the calendar month.
    Open rentals (no demobilize date) are counted through the month end."""
    start = max(getdate(rental_start), getdate(month_start))
    end = min(getdate(rental_end) if rental_end else getdate(month_end), getdate(month_end))
    if end < start:
        return 0
    return date_diff(end, start) + 1


class MonthlyBilling(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        from orion_erp.orion_erp.doctype.monthly_billing_fine_line.monthly_billing_fine_line import (
            MonthlyBillingFineLine,
        )
        from orion_erp.orion_erp.doctype.monthly_billing_salik_line.monthly_billing_salik_line import (
            MonthlyBillingSalikLine,
        )
        from orion_erp.orion_erp.doctype.monthly_billing_vehicle_line.monthly_billing_vehicle_line import (
            MonthlyBillingVehicleLine,
        )

        amended_from: DF.Link | None
        billing_month: DF.Date
        company: DF.Link | None
        customer: DF.Link
        external_invoice_ref: DF.Data | None
        fine_lines: DF.Table[MonthlyBillingFineLine]
        invoiced: DF.Check
        invoiced_date: DF.Date | None
        month_label: DF.Data | None
        remarks: DF.SmallText | None
        salik_lines: DF.Table[MonthlyBillingSalikLine]
        total_fine_amount: DF.Currency
        total_salik_amount: DF.Currency
        total_vehicle_days: DF.Int
        vehicle_lines: DF.Table[MonthlyBillingVehicleLine]
    # end: auto-generated types

    def autoname(self):
        self._normalize_month()
        self.name = f"MB-{self.customer}-{self.month_label}"

    def _normalize_month(self):
        """Snap billing_month to the 1st and derive the YYYY-MM label."""
        d = getdate(self.billing_month)
        self.billing_month = get_first_day(d)
        self.month_label = f"{d.year}-{d.month:02d}"

    def validate(self):
        self._normalize_month()
        self._check_unique()
        if self.invoiced and not (self.invoiced_date and self.external_invoice_ref):
            frappe.throw(_("Invoiced sheets need an invoiced date and an external invoice reference."))

    def _check_unique(self):
        filters = {
            "customer": self.customer,
            "billing_month": self.billing_month,
            "docstatus": ["<", 2],
        }
        # Exclude self only when editing an existing sheet; a brand-new sheet
        # shares the deterministic autoname with any existing one, so excluding
        # by name would hide the very duplicate we want to catch.
        if not self.is_new():
            filters["name"] = ["!=", self.name]
        dupe = frappe.db.exists("Monthly Billing", filters)
        if dupe:
            frappe.throw(
                _("A Monthly Billing sheet for {0} / {1} already exists: {2}").format(
                    self.customer, self.month_label, dupe
                )
            )

    # -- Build -------------------------------------------------------------
    def build(self):
        """(Re)compute all billable lines for this customer + month. Idempotent."""
        self._normalize_month()
        m_start = get_first_day(self.billing_month)
        m_end = get_last_day(self.billing_month)
        days_in_month = date_diff(m_end, m_start) + 1

        self.set("vehicle_lines", [])
        self.set("salik_lines", [])
        self.set("fine_lines", [])

        self._build_vehicle_lines(m_start, m_end, days_in_month)
        self._build_salik_lines(m_start, m_end)
        self._build_fine_lines(m_start, m_end)
        self._recompute_totals()

    def _build_vehicle_lines(self, m_start, m_end, days_in_month):
        rentals = frappe.get_all(
            "Vehicle Movement",
            filters={
                "docstatus": 1,
                "customer": self.customer,
                "movement_date": ["<=", m_end],
            },
            fields=["name", "vehicle", "rent_type", "movement_date", "demobilize_date"],
        )
        for r in rentals:
            # skip rentals that ended before this month started
            if r.demobilize_date and getdate(r.demobilize_date) < getdate(m_start):
                continue
            days = billable_days(r.movement_date, r.demobilize_date, m_start, m_end)
            if days <= 0:
                continue
            drivers = frappe.get_all(
                "Vehicle Movement Driver Shift",
                filters={"parent": r.name, "parenttype": "Vehicle Movement"},
                pluck="driver",
            )
            self.append(
                "vehicle_lines",
                {
                    "vehicle": r.vehicle,
                    "rental": r.name,
                    "rent_type": r.rent_type,
                    "drivers": ", ".join(d for d in drivers if d),
                    "period_from": max(getdate(r.movement_date), getdate(m_start)),
                    "period_to": min(
                        getdate(r.demobilize_date) if r.demobilize_date else getdate(m_end),
                        getdate(m_end),
                    ),
                    "billable_days": days,
                    "days_in_month": days_in_month,
                },
            )

    def _build_salik_lines(self, m_start, m_end):
        # Aggregate matched Salik Charge rows for this customer in this month.
        if not frappe.db.exists("DocType", "Salik Charge"):
            return
        charges = frappe.get_all(
            "Salik Charge",
            filters={
                "parenttype": "Salik or Darbs",
                "docstatus": 1,
                "customer": self.customer,
                "matched": 1,
                "charge_date": ["between", [m_start, m_end]],
            },
            fields=["vehicle", "parent as salik_batch", "amount"],
        )
        agg = {}
        for c in charges:
            key = (c.vehicle, c.salik_batch)
            row = agg.setdefault(key, {"txn_count": 0, "amount": 0.0})
            row["txn_count"] += 1
            row["amount"] += flt(c.amount)
        for (vehicle, batch), row in agg.items():
            self.append(
                "salik_lines",
                {"vehicle": vehicle, "salik_batch": batch, "txn_count": row["txn_count"], "amount": row["amount"]},
            )

    def _build_fine_lines(self, m_start, m_end):
        # Only fines the CUSTOMER is responsible for are billable.
        fines = frappe.get_all(
            "Traffic Fine or Accident",
            filters={
                "docstatus": 1,
                "customer": self.customer,
                "closing_status": "Paid by Client",
                "date": ["between", [m_start, m_end]],
            },
            fields=["name", "vehicle"],
        )
        has_total = frappe.db.has_column("Traffic Fine or Accident", "total_amount")
        for f in fines:
            amount = flt(frappe.db.get_value("Traffic Fine or Accident", f.name, "total_amount")) if has_total else 0.0
            fine_count = frappe.db.count("Fines cdt", {"parent": f.name, "parenttype": "Traffic Fine or Accident"})
            self.append(
                "fine_lines",
                {"traffic_fine": f.name, "vehicle": f.vehicle, "fine_count": fine_count or 1, "amount": amount},
            )

    def _recompute_totals(self):
        self.total_vehicle_days = sum(int(r.billable_days or 0) for r in self.vehicle_lines)
        self.total_salik_amount = sum(flt(r.amount) for r in self.salik_lines)
        self.total_fine_amount = sum(flt(r.amount) for r in self.fine_lines)


# ---------------------------------------------------------------------------
# Whitelisted actions
# ---------------------------------------------------------------------------
@frappe.whitelist()
def build(name):
    """Operations/auto: (re)build the billable lines on a draft sheet."""
    doc = frappe.get_doc("Monthly Billing", name)
    if doc.docstatus == 2:
        frappe.throw(_("Cannot build a cancelled sheet."))
    doc.build()
    doc.save(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def build_monthly_billing(customer, billing_month):
    """Create (if missing) + build + submit a Monthly Billing sheet for a
    customer and month. Returns the sheet name. Idempotent."""
    billing_month = get_first_day(getdate(billing_month))
    existing = frappe.db.get_value(
        "Monthly Billing",
        {"customer": customer, "billing_month": billing_month, "docstatus": ["<", 2]},
    )
    if existing:
        doc = frappe.get_doc("Monthly Billing", existing)
        if doc.docstatus == 0:
            doc.build()
            doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(
        {
            "doctype": "Monthly Billing",
            "customer": customer,
            "billing_month": billing_month,
        }
    )
    doc.build()
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


@frappe.whitelist()
def mark_invoiced(name, invoiced_date, external_invoice_ref):
    """Accounts-only: mark a submitted sheet as invoiced (date + external ref)."""
    frappe.only_for(("Accounts Manager", "System Manager"))
    if not external_invoice_ref:
        frappe.throw(_("An external invoice reference is required."))
    doc = frappe.get_doc("Monthly Billing", name)
    if doc.docstatus != 1:
        frappe.throw(_("Only a submitted sheet can be marked invoiced."))
    if doc.invoiced:
        frappe.throw(_("This month is already marked invoiced."))
    doc.db_set("invoiced", 1, update_modified=True)
    doc.db_set("invoiced_date", getdate(invoiced_date), update_modified=True)
    doc.db_set("external_invoice_ref", external_invoice_ref, update_modified=True)
    return doc.name


# ---------------------------------------------------------------------------
# Month-close scheduled job — never miss a month
# ---------------------------------------------------------------------------
def create_monthly_billing_sheets():
    """Run on the 1st: build Draft/Submitted sheets for the just-ended month for
    every customer that had any rental activity. Idempotent per (customer, month)."""
    today = getdate(frappe.utils.nowdate())
    prev_month = get_first_day(add_months(today, -1))
    m_start = get_first_day(prev_month)
    m_end = get_last_day(prev_month)

    customers = set()
    rentals = frappe.get_all(
        "Vehicle Movement",
        filters={"docstatus": 1, "movement_date": ["<=", m_end]},
        fields=["customer", "demobilize_date"],
    )
    for r in rentals:
        if r.customer and not (r.demobilize_date and getdate(r.demobilize_date) < m_start):
            customers.add(r.customer)

    for customer in customers:
        try:
            build_monthly_billing(customer, prev_month)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.log_error(
                frappe.get_traceback(),
                f"create_monthly_billing_sheets failed for {customer} / {prev_month}",
            )
