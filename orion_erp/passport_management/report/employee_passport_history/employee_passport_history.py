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
            "label": _("Document"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Passport Movement",
            "width": 160,
        },
        {
            "label": _("Movement Type"),
            "fieldname": "movement_type",
            "fieldtype": "Data",
            "width": 110,
        },
        {
            "label": _("Employee"),
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120,
        },
        {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Passport No."),
            "fieldname": "passport_number",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 140,
        },
        {
            "label": _("Transaction Date"),
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Purpose"),
            "fieldname": "purpose",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Expected Return"),
            "fieldname": "expected_return_date",
            "fieldtype": "Date",
            "width": 130,
        },
        {
            "label": _("Actual Return"),
            "fieldname": "actual_return_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Status"),
            "fieldname": "current_status",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Received By"),
            "fieldname": "received_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 140,
        },
    ]


def _get_data(filters):
    conditions = ["pm.docstatus IN (1, 2)"]
    values = {}

    if filters.get("employee"):
        conditions.append("pm.employee = %(employee)s")
        values["employee"] = filters["employee"]

    if filters.get("from_date"):
        conditions.append("pm.transaction_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("pm.transaction_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    if filters.get("movement_type"):
        conditions.append("pm.movement_type = %(movement_type)s")
        values["movement_type"] = filters["movement_type"]

    where_clause = " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            pm.name, pm.movement_type, pm.employee, pm.employee_name,
            pm.passport_number, pm.department, pm.transaction_date,
            pm.purpose, pm.expected_return_date, pm.actual_return_date,
            pm.current_status, pm.received_by
        FROM `tabPassport Movement` pm
        WHERE {where_clause}
        ORDER BY pm.employee, pm.transaction_date DESC
        """,
        values,
        as_dict=True,
    )
