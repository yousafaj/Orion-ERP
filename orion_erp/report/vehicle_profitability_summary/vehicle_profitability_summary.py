# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    columns = get_columns()
    data = []

    if not from_date or not to_date:
        return columns, data

    # --- 1) SALES per vehicle (signed: returns negative) ---
    sales_rows = frappe.db.sql(
        """
        SELECT
            sii.custom_vehicle AS vehicle,
            SUM(
                CASE WHEN si.is_return = 1
                     THEN -ABS(sii.amount)
                     ELSE  ABS(sii.amount)
                END
            ) AS total_sales
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %s AND %s
          AND sii.custom_vehicle IS NOT NULL AND sii.custom_vehicle <> ''
        GROUP BY sii.custom_vehicle
        """,
        (from_date, to_date),
        as_dict=True,
    )

    # --- 2) PURCHASE per vehicle (signed: returns negative) ---
    purchase_rows = frappe.db.sql(
        """
        SELECT
            pii.custom_vehicle AS vehicle,
            SUM(
                CASE WHEN pi.is_return = 1
                     THEN -ABS(pii.amount)
                     ELSE  ABS(pii.amount)
                END
            ) AS total_purchase
        FROM `tabPurchase Invoice` pi
        JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
        WHERE pi.docstatus = 1
          AND pi.posting_date BETWEEN %s AND %s
          AND pii.custom_vehicle IS NOT NULL AND pii.custom_vehicle <> ''
        GROUP BY pii.custom_vehicle
        """,
        (from_date, to_date),
        as_dict=True,
    )

    # --- 3) JOURNAL per vehicle (separate debit / credit sums) ---
    jv_rows = frappe.db.sql(
        """
        SELECT
            jve.custom_vehicle AS vehicle,
            SUM(COALESCE(jve.debit_in_account_currency, 0))  AS total_jd,
            SUM(COALESCE(jve.credit_in_account_currency, 0)) AS total_jc
        FROM `tabJournal Entry` jv
        JOIN `tabJournal Entry Account` jve ON jve.parent = jv.name
        WHERE jv.docstatus = 1
          AND jv.posting_date BETWEEN %s AND %s
          AND jve.custom_vehicle IS NOT NULL AND jve.custom_vehicle <> ''
        GROUP BY jve.custom_vehicle
        """,
        (from_date, to_date),
        as_dict=True,
    )

    # Merge buckets by vehicle
    agg = {}

    def ensure(vname: str):
        if vname not in agg:
            agg[vname] = {
                "vehicle": vname,
                "total_sales": 0.0,
                "total_purchase": 0.0,
                "total_jd": 0.0,
                "total_jc": 0.0,
            }
        return agg[vname]

    for r in sales_rows:
        row = ensure(r["vehicle"])
        row["total_sales"] = flt(r["total_sales"])

    for r in purchase_rows:
        row = ensure(r["vehicle"])
        row["total_purchase"] = flt(r["total_purchase"])

    for r in jv_rows:
        row = ensure(r["vehicle"])
        row["total_jd"] = flt(r["total_jd"])
        row["total_jc"] = flt(r["total_jc"])

    if not agg:
        return columns, data

    # Fetch Vehicle meta (Vehicle Num + Department)
    vehicle_names = list(agg.keys())
    vehicle_meta = {}
    for v in frappe.get_all(
        "Vehicle",
        fields=["name", "license_plate", "custom_ownership_status"],
        filters={"name": ["in", vehicle_names]},
        limit_page_length=0,
    ):
        vehicle_meta[v.name] = v

    # Build final rows
    for vname, r in agg.items():
        meta = vehicle_meta.get(vname, {})
        vehicle_num = (meta.get("license_plate") or "").strip() or vname
        department = meta.get("custom_ownership_status") or ""

        total_sales = flt(r["total_sales"])
        total_purchase = flt(r["total_purchase"])
        total_jd = flt(r["total_jd"])     # debit (reduces profit)
        total_jc = flt(r["total_jc"])     # credit (increases profit)

        gross_profit = total_sales - total_purchase - total_jd + total_jc

        data.append([
            vehicle_num,            # Vehicle Num
            department,             # Department
            total_sales,            # Total Sales (signed)
            total_purchase,         # Total Purchase (signed)
            total_jd,               # Total Journal Debit (absolute sum)
            total_jc,               # Total Journal Credit (absolute sum)
            gross_profit,           # Gross Profit
        ])

    # Sort by Vehicle Num for nicer UX
    data.sort(key=lambda x: (x[0] or ""))

    return columns, data


def get_columns():
    return [
        {"label": "Vehicle Num",          "fieldname": "vehicle_num",     "fieldtype": "Data",     "width": 140},
        {"label": "Department",           "fieldname": "department",      "fieldtype": "Link",     "options": "Department", "width": 160},
        {"label": "Total Sales",          "fieldname": "total_sales",     "fieldtype": "Currency", "width": 130},
        {"label": "Total Purchase",       "fieldname": "total_purchase",  "fieldtype": "Currency", "width": 140},
        {"label": "Total Journal Debit",  "fieldname": "total_jd",        "fieldtype": "Currency", "width": 160},
        {"label": "Total Journal Credit", "fieldname": "total_jc",        "fieldtype": "Currency", "width": 160},
        {"label": "Gross Profit",         "fieldname": "gross_profit",    "fieldtype": "Currency", "width": 140},
    ]
