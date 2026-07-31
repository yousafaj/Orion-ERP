import frappe
from frappe.utils import getdate, today


APPROVAL_FLOW = [
    {"approver_field": "leave_approver", "status_field": "status"},
    {"approver_field": "custom_leave_approver_1", "status_field": "custom_status_approver1"},
    {"approver_field": "custom_leave_approver_2", "status_field": "custom_status_approver2"},
    {"approver_field": "custom_leave_approver_4", "status_field": "custom_status_approver4"},
    {"approver_field": "custom_leave_approver_5", "status_field": "custom_status_approver5"},
]


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Leave Application", "fieldname": "name", "fieldtype": "Link", "options": "Leave Application", "width": 160},
        {"label": "Leave Type", "fieldname": "leave_type", "fieldtype": "Link", "options": "Leave Type", "width": 150},
        {"label": "From Date", "fieldname": "from_date", "fieldtype": "Date", "width": 110},
        {"label": "To Date", "fieldname": "to_date", "fieldtype": "Date", "width": 110},
        {"label": "Days Taken", "fieldname": "total_leave_days", "fieldtype": "Float", "width": 110},
        {"label": "Pay Type", "fieldname": "pay_type", "fieldtype": "Data", "width": 100},
        {"label": "Approved By", "fieldname": "approved_by", "fieldtype": "Data", "width": 180},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": "Document", "fieldname": "document", "fieldtype": "Data", "width": 200},
    ]


def get_data(filters):
    filters = filters or {}
    conditions = []
    values = {}

    if filters.get("from_date"):
        conditions.append("la.from_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("la.to_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]
    if filters.get("employee"):
        conditions.append("la.employee = %(employee)s")
        values["employee"] = filters["employee"]
    if filters.get("department"):
        conditions.append("la.department = %(department)s")
        values["department"] = filters["department"]
    if filters.get("leave_type"):
        conditions.append("la.leave_type = %(leave_type)s")
        values["leave_type"] = filters["leave_type"]

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    data = frappe.db.sql(
        f"""
        SELECT
            la.name,
            la.leave_type,
            la.from_date,
            la.to_date,
            la.total_leave_days,
            la.docstatus,
            la.leave_approver,
            la.leave_approver_name,
            la.custom_leave_approver_1,
            la.custom_leave_approver_2,
            la.custom_leave_approver_4,
            la.custom_leave_approver_5,
            la.status AS approver1_status,
            la.custom_status_approver1,
            la.custom_status_approver2,
            la.custom_status_approver4,
            la.custom_status_approver5,
            la.custom_medical_certificate,
            la.custom_child_birth_certificate,
            la.custom_approval_status,
            lt.is_lwp,
            lt.is_ppl
        FROM `tabLeave Application` la
        LEFT JOIN `tabLeave Type` lt ON lt.name = la.leave_type
        WHERE {where_clause}
        ORDER BY la.from_date DESC
        """,
        values,
        as_dict=1,
    )

    today_date = getdate(today())
    approver_user_map = _get_approver_names(data)

    for row in data:
        row["pay_type"] = _get_pay_type(row)
        row["approved_by"] = _get_approved_by(row, approver_user_map)
        row["status"] = _get_availed_status(row, today_date)
        row["document"] = _get_document_link(row)

    return data


def _get_approver_names(rows):
    user_ids = set()
    for row in rows:
        for step in APPROVAL_FLOW:
            uid = row.get(step["approver_field"])
            if uid:
                user_ids.add(uid)
    if not user_ids:
        return {}
    names = frappe.db.sql(
        "SELECT name, full_name FROM `tabUser` WHERE name IN %(users)s",
        {"users": list(user_ids)},
        as_dict=1,
    )
    return {u.name: u.full_name for u in names}


def _get_pay_type(row):
    if row.get("is_lwp"):
        return "Unpaid"
    if row.get("is_ppl"):
        return "Half Pay"
    return "Full Pay"


def _get_approved_by(row, user_map):
    for step in reversed(APPROVAL_FLOW):
        status = row.get(step["status_field"])
        if status == "Approved":
            approver = row.get(step["approver_field"])
            if approver:
                return user_map.get(approver, approver)
    return ""


def _get_availed_status(row, today_date):
    app_status = row.get("custom_approval_status") or ""
    if app_status:
        return app_status
    if row.docstatus == 2:
        return "Cancelled"
    if row.docstatus == 0:
        return "Open"
    return row.get("approver1_status") or ""


def _get_document_link(row):
    docs = []
    if row.get("custom_medical_certificate"):
        docs.append(f'<a href="{row.custom_medical_certificate}" target="_blank">Medical Certificate</a>')
    if row.get("custom_child_birth_certificate"):
        docs.append(f'<a href="{row.custom_child_birth_certificate}" target="_blank">Child Birth Certificate</a>')
    return ", ".join(docs) if docs else ""
