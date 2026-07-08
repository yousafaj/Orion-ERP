# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    filters = filters or {}

    if not filters.get("from_date") or not filters.get("to_date"):
        return get_columns(), []

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Vehicle No",
            "fieldname": "vehicle",
            "fieldtype": "Link",
            "options": "Vehicle",
            "width": 180
        },
        {
            "label": "Sales Amount",
            "fieldname": "sales_amount",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "Purchase Amount",
            "fieldname": "purchase_amount",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "JV Debit Amount",
            "fieldname": "jv_debit_amount",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "JV Credit Amount",
            "fieldname": "jv_credit_amount",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "Gross Profit",
            "fieldname": "gross_profit",
            "fieldtype": "Currency",
            "width": 150
        }
    ]


def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    company = filters.get("company")
    cost_center = filters.get("cost_center")
    vehicle = filters.get("vehicle")

    outer_params = []
    outer_conditions = ""

    if vehicle:
        outer_conditions += " AND v.name = %s"
        outer_params.append(vehicle)

    subquery_params = []

    sales_subquery = """
        SELECT
            sii.vehicle_details,
            SUM(sii.amount) AS sales_amount
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si
            ON si.name = sii.parent
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %s AND %s
          AND si.company = %s
    """
    subquery_params.extend([from_date, to_date, company])

    if cost_center:
        sales_subquery += " AND sii.cost_center = %s"
        subquery_params.append(cost_center)

    sales_subquery += " GROUP BY sii.vehicle_details"

    purchase_subquery = """
        SELECT
            pii.vehicle_details,
            SUM(pii.amount) AS purchase_amount
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi
            ON pi.name = pii.parent
        WHERE pi.docstatus = 1
          AND pi.posting_date BETWEEN %s AND %s
          AND pi.company = %s
    """
    subquery_params.extend([from_date, to_date, company])

    if cost_center:
        purchase_subquery += " AND pii.cost_center = %s"
        subquery_params.append(cost_center)

    purchase_subquery += " GROUP BY pii.vehicle_details"

    jv_subquery = """
        SELECT
            jea.vehicle_details,
            SUM(CASE WHEN jea.debit > 0 THEN jea.debit ELSE 0 END) AS jv_debit_amount,
            SUM(CASE WHEN jea.credit > 0 THEN jea.credit ELSE 0 END) AS jv_credit_amount
        FROM `tabJournal Entry Account` jea
        INNER JOIN `tabJournal Entry` je
            ON je.name = jea.parent
        WHERE je.docstatus = 1
          AND je.posting_date BETWEEN %s AND %s
          AND je.company = %s
    """
    subquery_params.extend([from_date, to_date, company])

    if cost_center:
        jv_subquery += " AND jea.cost_center = %s"
        subquery_params.append(cost_center)

    jv_subquery += " GROUP BY jea.vehicle_details"

    query = f"""
        SELECT
            v.name AS vehicle,
            COALESCE(s.sales_amount, 0) AS sales_amount,
            COALESCE(p.purchase_amount, 0) AS purchase_amount,
            COALESCE(j.jv_debit_amount, 0) AS jv_debit_amount,
            COALESCE(j.jv_credit_amount, 0) AS jv_credit_amount,
            (
                COALESCE(s.sales_amount, 0)
                - COALESCE(p.purchase_amount, 0)
                - COALESCE(j.jv_debit_amount, 0)
                + COALESCE(j.jv_credit_amount, 0)
            ) AS gross_profit
        FROM `tabVehicle` v
        LEFT JOIN ({sales_subquery}) s
            ON s.vehicle_details = v.name
        LEFT JOIN ({purchase_subquery}) p
            ON p.vehicle_details = v.name
        LEFT JOIN ({jv_subquery}) j
            ON j.vehicle_details = v.name
        WHERE 1=1
        {outer_conditions}
        ORDER BY v.name
    """

    return frappe.db.sql(query, tuple(subquery_params + outer_params), as_dict=True)
