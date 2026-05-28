# Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = []

    vehicle = filters.get("vehicke")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    # ---- Fetch Sales Transactions ----
    sales = frappe.db.sql("""
        SELECT
            si.name AS docname,
            si.posting_date,
            si.is_return,
            sii.description AS ref,
            sii.item_name AS details,
            sii.amount AS item_amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.posting_date BETWEEN %s AND %s
          AND sii.custom_vehicle = %s
          AND si.docstatus = 1
    """, (from_date, to_date, vehicle), as_dict=1)

    for s in sales:
        tran_code = "SC" if s.is_return else "SI"
        tran_type = "Sales Credit" if s.is_return else "Sales Invoice"
        amount = -abs(flt(s.item_amount)) if s.is_return else abs(flt(s.item_amount))

        data.append([
            s.docname,       # Tran No
            tran_code,       # Tran Code
            tran_type,       # Transaction Type
            s.posting_date,  # Date
            s.ref,           # Reference
            s.details,       # Details
            amount           # Actual Net
        ])

    # ---- Fetch Purchase Transactions ----
    purchases = frappe.db.sql("""
        SELECT
            pi.name AS docname,
            pi.posting_date,
            pi.is_return,
            pii.description AS ref,
            pii.item_name AS details,
            pii.amount AS item_amount
        FROM `tabPurchase Invoice` pi
        JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
        WHERE pi.posting_date BETWEEN %s AND %s
          AND pii.custom_vehicle = %s
          AND pi.docstatus = 1
    """, (from_date, to_date, vehicle), as_dict=1)

    for p in purchases:
        tran_code = "PC" if p.is_return else "PI"
        tran_type = "Purchase Credit" if p.is_return else "Purchase Invoice"
        amount = -abs(flt(p.item_amount)) if p.is_return else abs(flt(p.item_amount))

        data.append([
            p.docname,       # Tran No
            tran_code,       # Tran Code
            tran_type,       # Transaction Type
            p.posting_date,  # Date
            p.ref,           # Reference
            p.details,       # Details
            amount           # Actual Net
        ])

    # ---- Fetch Journal Vouchers ----
    jvs = frappe.db.sql("""
        SELECT
            jv.name AS docname,
            jv.posting_date,
            jve.debit_in_account_currency  AS debit,
            jve.credit_in_account_currency AS credit,
            jve.user_remark AS ref,
            jve.account AS details
        FROM `tabJournal Entry` jv
        JOIN `tabJournal Entry Account` jve ON jve.parent = jv.name
        WHERE jv.posting_date BETWEEN %s AND %s
          AND jve.custom_vehicle = %s
          AND jv.docstatus = 1
    """, (from_date, to_date, vehicle), as_dict=1)

    for j in jvs:
        debit = flt(j.debit)
        credit = flt(j.credit)

        if debit > 0 and credit <= 0:
            tran_code, tran_type = "JD", "Journal Debit"
            amount = debit
        elif credit > 0 and debit <= 0:
            tran_code, tran_type = "JC", "Journal Credit"
            amount = -credit
        else:
            if debit > credit:
                tran_code, tran_type = "JD", "Journal Debit"
                amount = debit - credit
            elif credit > debit:
                tran_code, tran_type = "JC", "Journal Credit"
                amount = -(credit - debit)
            else:
                tran_code, tran_type = "JV", "Journal Entry"
                amount = 0

        data.append([
            j.docname,       # Tran No
            tran_code,       # Tran Code
            tran_type,       # Transaction Type
            j.posting_date,  # Date
            j.ref,           # Reference
            j.details,       # Details (account)
            amount           # Actual Net (+debit, -credit)
        ])
        
    # ---- Summary (Totals + Profit) ----
    total_sales = 0.0
    total_purchase = 0.0
    total_jvs = 0.0

    # data rows are lists: [0]=docname, [1]=tran_code, [2]=tran_type, [6]=amount
    for row in data:
        tran_code = (row[1] or "").upper()
        amount = flt(row[6])

        if tran_code in ("SI", "SC"):       # Sales Invoice / Sales Credit (signed already)
            total_sales += amount
        elif tran_code in ("PI", "PC"):     # Purchase Invoice / Purchase Credit (signed already)
            total_purchase += amount
        elif tran_code in ("JD", "JC"):     # Journal Debit / Journal Credit (signed: +debit, -credit)
            total_jvs += amount

    vehicle_profit = total_sales - total_purchase - total_jvs

    # spacer row
    data.append([None, None, None, None, None, None, None])

    # summary rows (put label in "Transaction Type" column and value in "Actual Net")
    data.append([None, None, "Total Sales",       None, None, None, flt(total_sales)])
    data.append([None, None, "Total Purchase",    None, None, None, flt(total_purchase)])
    data.append([None, None, "Total JVs:",        None, None, None, flt(total_jvs)])
    data.append([None, None, "Vehicle profit",    None, None, None, flt(vehicle_profit)])

    return columns, data

    return columns, data


def get_columns():
    return [
        {"label": "Tran No",          "fieldname": "docname",      "fieldtype": "Data",     "width": 150},
        {"label": "Tran Code",        "fieldname": "tran_code",    "fieldtype": "Data",     "width": 100},
        {"label": "Transaction Type", "fieldname": "tran_type",    "fieldtype": "Data",     "width": 150},
        {"label": "Date",             "fieldname": "posting_date", "fieldtype": "Date",     "width": 120},
        {"label": "Reference",        "fieldname": "ref",          "fieldtype": "Data",     "width": 180},
        {"label": "Details",          "fieldname": "details",      "fieldtype": "Data",     "width": 220},
        {"label": "Actual Net",       "fieldname": "amount",       "fieldtype": "Currency", "width": 120},
    ]
