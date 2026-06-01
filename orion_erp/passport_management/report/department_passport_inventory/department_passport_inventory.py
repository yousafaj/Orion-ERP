import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = _get_columns()
    data = _get_data(filters)
    return columns, data


def _get_columns():
    return [
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 180,
        },
        {
            "label": _("Active Passports"),
            "fieldname": "active_passports",
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "label": _("With Company"),
            "fieldname": "with_company",
            "fieldtype": "Int",
            "width": 130,
        },
        {
            "label": _("Embassy Submission"),
            "fieldname": "embassy_submission",
            "fieldtype": "Int",
            "width": 160,
        },
        {
            "label": _("Under Processing"),
            "fieldname": "under_processing",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": _("Renewal Process"),
            "fieldname": "renewal_process",
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "label": _("Overdue Returns"),
            "fieldname": "overdue",
            "fieldtype": "Int",
            "width": 140,
        },
    ]


def _get_data(filters):
    rows = frappe.db.sql(
        """
        SELECT
            department,
            COUNT(*) AS active_passports,
            SUM(CASE WHEN current_status = 'With Company'       THEN 1 ELSE 0 END) AS with_company,
            SUM(CASE WHEN current_status = 'Embassy Submission' THEN 1 ELSE 0 END) AS embassy_submission,
            SUM(CASE WHEN current_status = 'Under Processing'   THEN 1 ELSE 0 END) AS under_processing,
            SUM(CASE WHEN current_status = 'Renewal Process'    THEN 1 ELSE 0 END) AS renewal_process,
            SUM(CASE
                WHEN expected_return_date IS NOT NULL
                 AND expected_return_date < CURDATE()
                THEN 1 ELSE 0
            END) AS overdue
        FROM `tabPassport Movement`
        WHERE movement_type = 'In'
          AND is_active_record = 1
          AND docstatus = 1
        GROUP BY department
        ORDER BY active_passports DESC
        """,
        as_dict=True,
    )
    return rows
