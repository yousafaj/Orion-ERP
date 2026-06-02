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
            "label": _("Designation"),
            "fieldname": "designation",
            "fieldtype": "Link",
            "options": "Designation",
            "width": 140,
        },
        {
            "label": _("Collection Date"),
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Expected Return"),
            "fieldname": "expected_return_date",
            "fieldtype": "Date",
            "width": 130,
        },
        {
            "label": _("Status"),
            "fieldname": "current_status",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Purpose"),
            "fieldname": "purpose",
            "fieldtype": "Data",
            "width": 200,
        },
    ]


def _get_data(filters):
    conditions = ["pm.movement_type = 'In'", "pm.is_active_record = 1", "pm.docstatus = 1"]
    values = {}

    if filters.get("department"):
        conditions.append("pm.department = %(department)s")
        values["department"] = filters["department"]

    if filters.get("employee"):
        conditions.append("pm.employee = %(employee)s")
        values["employee"] = filters["employee"]

    where_clause = " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            pm.name, pm.employee, pm.employee_name, pm.passport_number,
            pm.department, pm.designation, pm.transaction_date,
            pm.expected_return_date, pm.current_status, pm.purpose
        FROM `tabPassport Movement` pm
        WHERE {where_clause}
        ORDER BY pm.transaction_date ASC
        """,
        values,
        as_dict=True,
    )
