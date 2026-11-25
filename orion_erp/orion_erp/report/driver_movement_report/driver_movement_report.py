import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today


def execute(filters=None):
    filters = frappe._dict(filters or {})

    # One person can have more than one Pre-Employment Training record: include all of them.
    if filters.get("driver"):
        emp = frappe.db.get_value("Pre-Employment Training", filters.driver, "employee_id")
        filters.driver_in = (
            frappe.get_all("Pre-Employment Training", filters={"employee_id": emp}, pluck="name")
            if emp else [filters.driver]
        )

    data = get_data(filters)
    return get_columns(), data, None, None, get_summary(data)


def get_columns():
    return [
        {"label": _("Driver"), "fieldname": "driver_name", "fieldtype": "Data", "width": 170},
        {"label": _("Employee ID"), "fieldname": "employee_id", "fieldtype": "Data", "width": 110},
        {"label": _("Now"), "fieldname": "current_status", "fieldtype": "Data", "width": 120},
        {"label": _("Current Vehicle"), "fieldname": "current_vehicle", "fieldtype": "Data", "width": 120},
        {"label": _("Current Customer"), "fieldname": "current_customer", "fieldtype": "Data", "width": 210},
        {"label": _("Current Site"), "fieldname": "current_site", "fieldtype": "Data", "width": 130},
        {"label": _("Site Location"), "fieldname": "current_site_location", "fieldtype": "Data", "width": 130},
        {"label": _("Since"), "fieldname": "since", "fieldtype": "Date", "width": 105},
        {"label": _("Deployments"), "fieldname": "total_deployments", "fieldtype": "Int", "width": 100},
        {"label": _("Vehicles"), "fieldname": "vehicle_count", "fieldtype": "Int", "width": 80},
        {"label": _("Clients"), "fieldname": "client_count", "fieldtype": "Int", "width": 75},
        {"label": _("Total Days"), "fieldname": "total_days", "fieldtype": "Int", "width": 90},
        {"label": _("Last Demobilized"), "fieldname": "last_demobilized", "fieldtype": "Date", "width": 120},
    ]


def get_data(filters):
    conds = [["Vehicle Deployment", "docstatus", "<", 2]]
    if filters.get("driver_in"):
        conds.append(["Vehicle Deployment", "driver", "in", filters.driver_in])
    if filters.get("vehicle"):
        conds.append(["Vehicle Deployment", "vehicle", "=", filters.vehicle])
    if filters.get("customer"):
        conds.append(["Vehicle Deployment", "customer", "=", filters.customer])
    if filters.get("driver_name"):
        conds.append(["Vehicle Deployment", "driver_name", "like", f"%{filters.driver_name}%"])
    if filters.get("from_date"):
        conds.append(["Vehicle Deployment", "mobilization_date", ">=", filters.from_date])
    if filters.get("to_date"):
        conds.append(["Vehicle Deployment", "mobilization_date", "<=", filters.to_date])

    deps = frappe.get_all(
        "Vehicle Deployment",
        filters=conds,
        fields=[
            "name", "vehicle", "driver", "driver_name", "customer", "site", "site_location",
            "mobilization_date", "actual_end_date", "status", "creation",
        ],
        limit_page_length=0,
    )

    # a driver (person) = the Employee behind the Pre-Employment Training record
    pet_ids = {d.driver for d in deps if d.driver}
    key_of, emp_of = {}, {}
    if pet_ids:
        for p in frappe.get_all(
            "Pre-Employment Training",
            filters={"name": ["in", list(pet_ids)]},
            fields=["name", "employee_id"],
            limit_page_length=0,
        ):
            key_of[p.name] = p.employee_id or p.name
            emp_of[p.name] = p.employee_id or ""

    by_driver = {}
    for d in deps:
        if d.driver:
            by_driver.setdefault(key_of.get(d.driver, d.driver), []).append(d)

    def start(d):
        return d.mobilization_date or getdate(d.creation)

    rows = []
    for key, items in by_driver.items():
        items.sort(key=lambda d: (str(start(d)), str(d.creation)))
        latest = items[-1]
        current = next((d for d in reversed(items) if d.status == "Mobilized"), None)
        ended = [d.actual_end_date for d in items if d.actual_end_date]
        name = next((d.driver_name for d in reversed(items) if d.driver_name), None) or key

        rows.append({
            "driver_name": name,
            "driver_id": latest.driver,                   # used by the popup
            "employee_id": emp_of.get(latest.driver, ""),
            "current_status": "On Deployment" if current else "Free",
            "current_vehicle": current.vehicle if current else "",
            "current_customer": current.customer if current else "",
            "current_site": current.site if current else "",
            "current_site_location": current.site_location if current else "",
            "since": start(current) if current else None,
            "total_deployments": len(items),
            "vehicle_count": len({d.vehicle for d in items if d.vehicle}),
            "client_count": len({d.customer for d in items if d.customer}),
            "total_days": sum(date_diff(d.actual_end_date or today(), start(d)) + 1 for d in items),
            "last_demobilized": max(ended) if ended else None,
        })

    if filters.get("current_status"):
        rows = [r for r in rows if r["current_status"] == filters.current_status]
    rows.sort(key=lambda r: (r["driver_name"] or "").lower())
    return rows


def get_summary(data):
    if not data:
        return []
    on = len([r for r in data if r["current_status"] == "On Deployment"])
    return [
        {"value": len(data), "label": _("Drivers"), "datatype": "Int"},
        {"value": on, "label": _("On Deployment"), "datatype": "Int", "indicator": "Green"},
        {"value": len(data) - on, "label": _("Free"), "datatype": "Int", "indicator": "Blue"},
        {"value": sum(r["total_deployments"] for r in data), "label": _("Deployments"), "datatype": "Int"},
    ]