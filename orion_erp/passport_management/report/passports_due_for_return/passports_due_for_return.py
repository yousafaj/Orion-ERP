import frappe
from frappe import _
from frappe.utils import add_days, today


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
            "label": _("Days Until Due"),
            "fieldname": "days_until_due",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": _("Status"),
            "fieldname": "current_status",
            "fieldtype": "Data",
            "width": 150,
        },
    ]


def _get_data(filters):
    # Default: due within the next 30 days
    due_within_days = int(filters.get("due_within_days", 30))
    cutoff_date = add_days(today(), due_within_days)

    conditions = [
        "pm.movement_type = 'In'",
        "pm.is_active_record = 1",
        "pm.docstatus = 1",
        "pm.expected_return_date IS NOT NULL",
        "pm.expected_return_date <= %(cutoff_date)s",
    ]
    values = {"cutoff_date": cutoff_date, "today": today()}

    if filters.get("department"):
        conditions.append("pm.department = %(department)s")
        values["department"] = filters["department"]

    where_clause = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            pm.name, pm.employee, pm.employee_name, pm.passport_number,
            pm.department, pm.transaction_date, pm.expected_return_date,
            pm.current_status,
            DATEDIFF(pm.expected_return_date, %(today)s) AS days_until_due
        FROM `tabPassport Movement` pm
        WHERE {where_clause}
        ORDER BY pm.expected_return_date ASC
        """,
        values,
        as_dict=True,
    )
    return rows
