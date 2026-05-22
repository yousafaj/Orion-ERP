import frappe
from frappe.utils import today


def execute(filters=None):
    """
    Entry point for the Script Report.

    Returns:
        tuple: columns definition and filtered data.
    """
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    """
    Define report columns displayed in the report view.
    """

    return [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
        {"label": "Employee Category", "fieldname": "employee_category", "fieldtype": "Data", "width": 150},
        {"label": "Leave Type", "fieldname": "leave_type", "fieldtype": "Link", "options": "Leave Type", "width": 150},
        {"label": "From Date", "fieldname": "from_date", "fieldtype": "Date", "width": 120},
        {"label": "To Date", "fieldname": "to_date", "fieldtype": "Date", "width": 120},
        {"label": "Total Days", "fieldname": "total_leave_days", "fieldtype": "Float", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
    ]


def get_data(filters):
    """
    Fetch leave application data based on provided filters.

    Args:
        filters (dict): Report filters from UI.

    Returns:
        list: Filtered leave application records.
    """

    # Base conditions for approved leave applications of active employees
    conditions = """
        WHERE la.docstatus = 1
        AND la.status = 'Approved'
        AND emp.status = 'Active'
    """

    values = {}

    # Filter by overlapping date range
    if filters.get("from_date") and filters.get("to_date"):
        conditions += """
            AND la.from_date <= %(to_date)s
            AND la.to_date >= %(from_date)s
        """
        values["from_date"] = filters.get("from_date")
        values["to_date"] = filters.get("to_date")

    # Filter by employee
    if filters.get("employee"):
        conditions += " AND la.employee = %(employee)s "
        values["employee"] = filters.get("employee")

    # Filter by department
    if filters.get("department"):
        conditions += " AND la.department = %(department)s "
        values["department"] = filters.get("department")

    # Filter by leave type
    if filters.get("leave_type"):
        conditions += " AND la.leave_type = %(leave_type)s "
        values["leave_type"] = filters.get("leave_type")

    # Filter by custom employee category
    if filters.get("employee_category"):
        conditions += " AND emp.custom_employee_category = %(employee_category)s "
        values["employee_category"] = filters.get("employee_category")

    # Fetch data using SQL query
    data = frappe.db.sql(
        f"""
        SELECT
            la.employee,
            la.employee_name,
            la.department,
            emp.custom_employee_category AS employee_category,
            la.leave_type,
            la.from_date,
            la.to_date,
            la.total_leave_days,
            la.status
        FROM `tabLeave Application` la
        LEFT JOIN `tabEmployee` emp ON emp.name = la.employee
        {conditions}
        ORDER BY la.from_date ASC
        """,
        values,
        as_dict=1,
    )

    return data