# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):

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

    conditions = ""

    if filters.get("vehicle"):
        conditions += f"""
            AND v.name = '{filters.get("vehicle")}'
        """

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

        LEFT JOIN (
            SELECT
                sii.vehicle_details,
                SUM(sii.amount) AS sales_amount

            FROM `tabSales Invoice Item` sii

            INNER JOIN `tabSales Invoice` si
                ON si.name = sii.parent

            WHERE si.docstatus = 1

            GROUP BY sii.vehicle_details
        ) s
        ON s.vehicle_details = v.name

        LEFT JOIN (
            SELECT
                pii.vehicle_details,
                SUM(pii.amount) AS purchase_amount

            FROM `tabPurchase Invoice Item` pii

            INNER JOIN `tabPurchase Invoice` pi
                ON pi.name = pii.parent

            WHERE pi.docstatus = 1

            GROUP BY pii.vehicle_details
        ) p
        ON p.vehicle_details = v.name

        LEFT JOIN (
            SELECT
                jea.vehicle_details,

                SUM(
                    CASE
                        WHEN jea.debit > 0
                        THEN jea.debit
                        ELSE 0
                    END
                ) AS jv_debit_amount,

                SUM(
                    CASE
                        WHEN jea.credit > 0
                        THEN jea.credit
                        ELSE 0
                    END
                ) AS jv_credit_amount

            FROM `tabJournal Entry Account` jea

            INNER JOIN `tabJournal Entry` je
                ON je.name = jea.parent

            WHERE je.docstatus = 1

            GROUP BY jea.vehicle_details
        ) j
        ON j.vehicle_details = v.name

        WHERE 1=1
        {conditions}

        ORDER BY v.name
    """

    return frappe.db.sql(query, as_dict=True)