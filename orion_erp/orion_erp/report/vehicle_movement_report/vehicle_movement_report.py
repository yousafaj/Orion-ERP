# import frappe
# from frappe import _
# from frappe.utils import date_diff, today

# VEHICLE_TYPE_FIELD = "custom_vehicle_type"


# def execute(filters=None):
#     filters = frappe._dict(filters or {})
#     data = get_data(filters)
#     return get_columns(), data, None, None, get_summary(data)


# def get_columns():
#     return [
#         {"label": _("Vehicle"), "fieldname": "vehicle", "fieldtype": "Data", "width": 110},
#         {"label": _("Type"), "fieldname": "vehicle_type", "fieldtype": "Data", "width": 110},
#         {"label": _("Make"), "fieldname": "make", "fieldtype": "Data", "width": 150},
#         {"label": _("Now"), "fieldname": "current_status", "fieldtype": "Data", "width": 120},
#         {"label": _("Current Driver"), "fieldname": "current_driver", "fieldtype": "Data", "width": 150},
#         {"label": _("Current Customer"), "fieldname": "current_customer", "fieldtype": "Data", "width": 210},
#         {"label": _("Current Site"), "fieldname": "current_site", "fieldtype": "Data", "width": 130},
#         {"label": _("Site Location"), "fieldname": "current_site_location", "fieldtype": "Data", "width": 130},
#         {"label": _("Since"), "fieldname": "since", "fieldtype": "Date", "width": 105},
#         {"label": _("Deployments"), "fieldname": "total_deployments", "fieldtype": "Int", "width": 100},
#         {"label": _("Drivers"), "fieldname": "driver_count", "fieldtype": "Int", "width": 75},
#         {"label": _("Clients"), "fieldname": "client_count", "fieldtype": "Int", "width": 75},
#         {"label": _("Total Days"), "fieldname": "total_days", "fieldtype": "Int", "width": 90},
#         {"label": _("Last Demobilized"), "fieldname": "last_demobilized", "fieldtype": "Date", "width": 120},
#     ]


# def get_data(filters):
#     conds = [["Vehicle Deployment", "docstatus", "<", 2]]
#     if filters.get("vehicle"):
#         conds.append(["Vehicle Deployment", "vehicle", "=", filters.vehicle])
#     if filters.get("customer"):
#         conds.append(["Vehicle Deployment", "customer", "=", filters.customer])
#     if filters.get("driver_name"):
#         conds.append(["Vehicle Deployment", "driver_name", "like", f"%{filters.driver_name}%"])
#     if filters.get("from_date"):
#         conds.append(["Vehicle Deployment", "mobilization_date", ">=", filters.from_date])
#     if filters.get("to_date"):
#         conds.append(["Vehicle Deployment", "mobilization_date", "<=", filters.to_date])

#     deps = frappe.get_all(
#         "Vehicle Deployment",
#         filters=conds,
#         fields=[
#             "name", "vehicle", "driver", "driver_name", "customer", "site", "site_location",
#             "mobilization_date", "actual_end_date", "status", "creation",
#         ],
#         limit_page_length=0,
#     )

#     by_vehicle = {}
#     for d in deps:
#         if d.vehicle:
#             by_vehicle.setdefault(d.vehicle, []).append(d)

#     info = {}
#     if by_vehicle:
#         for v in frappe.get_all(
#             "Vehicle",
#             filters={"name": ["in", list(by_vehicle)]},
#             fields=["name", VEHICLE_TYPE_FIELD, "make"],
#             limit_page_length=0,
#         ):
#             info[v.name] = v

#     rows = []
#     for vehicle in sorted(by_vehicle):
#         items = sorted(by_vehicle[vehicle], key=lambda d: (str(d.mobilization_date or ""), str(d.creation)))
#         current = next((d for d in reversed(items) if d.status == "Mobilized"), None)
#         ended = [d.actual_end_date for d in items if d.actual_end_date]
#         days = 0
#         for d in items:
#             if d.mobilization_date:
#                 days += date_diff(d.actual_end_date or today(), d.mobilization_date) + 1

#         v = info.get(vehicle) or {}
#         rows.append({
#             "vehicle": vehicle,
#             "vehicle_type": v.get(VEHICLE_TYPE_FIELD) or "",
#             "make": v.get("make") or "",
#             "current_status": "On Deployment" if current else "Free",
#             "current_driver": (current.driver_name or current.driver) if current else "",
#             "current_customer": current.customer if current else "",
#             "current_site": current.site if current else "",
#             "current_site_location": current.site_location if current else "",
#             "since": current.mobilization_date if current else None,
#             "total_deployments": len(items),
#             "driver_count": len({d.driver_name or d.driver for d in items if d.driver_name or d.driver}),
#             "client_count": len({d.customer for d in items if d.customer}),
#             "total_days": days,
#             "last_demobilized": max(ended) if ended else None,
#         })

#     if filters.get("current_status"):
#         rows = [r for r in rows if r["current_status"] == filters.current_status]
#     return rows


# def get_summary(data):
#     if not data:
#         return []
#     on = len([r for r in data if r["current_status"] == "On Deployment"])
#     return [
#         {"value": len(data), "label": _("Vehicles"), "datatype": "Int"},
#         {"value": on, "label": _("On Deployment"), "datatype": "Int", "indicator": "Green"},
#         {"value": len(data) - on, "label": _("Free"), "datatype": "Int", "indicator": "Orange"},
#         {"value": sum(r["total_deployments"] for r in data), "label": _("Deployments"), "datatype": "Int"},
#     ]





import frappe
from frappe import _
from frappe.utils import date_diff, today

VEHICLE_TYPE_FIELD = "custom_vehicle_type"
LOG = "Vehicle Status Log"      # child table of Vehicle (Workshop / Idle periods)


def execute(filters=None):
    filters = frappe._dict(filters or {})
    data = get_data(filters)
    return get_columns(), data, None, None, get_summary(data)


def get_columns():
    return [
        {"label": _("Vehicle"), "fieldname": "vehicle", "fieldtype": "Data", "width": 110},
        {"label": _("Type"), "fieldname": "vehicle_type", "fieldtype": "Data", "width": 110},
        {"label": _("Make"), "fieldname": "make", "fieldtype": "Data", "width": 150},
        {"label": _("Now"), "fieldname": "current_status", "fieldtype": "Data", "width": 120},
        {"label": _("Current Driver"), "fieldname": "current_driver", "fieldtype": "Data", "width": 150},
        {"label": _("Current Customer"), "fieldname": "current_customer", "fieldtype": "Data", "width": 210},
        {"label": _("Current Site"), "fieldname": "current_site", "fieldtype": "Data", "width": 130},
        {"label": _("Site Location"), "fieldname": "current_site_location", "fieldtype": "Data", "width": 130},
        {"label": _("Since"), "fieldname": "since", "fieldtype": "Date", "width": 105},
        {"label": _("Workshop / Idle Note"), "fieldname": "current_note", "fieldtype": "Data", "width": 200},
        {"label": _("Deployments"), "fieldname": "total_deployments", "fieldtype": "Int", "width": 100},
        {"label": _("Drivers"), "fieldname": "driver_count", "fieldtype": "Int", "width": 75},
        {"label": _("Clients"), "fieldname": "client_count", "fieldtype": "Int", "width": 75},
        {"label": _("Days Deployed"), "fieldname": "total_days", "fieldtype": "Int", "width": 100},
        {"label": _("Days in Workshop"), "fieldname": "workshop_days", "fieldtype": "Int", "width": 115},
        {"label": _("Days Idle"), "fieldname": "idle_days", "fieldtype": "Int", "width": 85},
        {"label": _("Last Demobilized"), "fieldname": "last_demobilized", "fieldtype": "Date", "width": 120},
    ]


def _days(frm, to):
    """Days of a period, counting both the first and the last day."""
    return date_diff(to or today(), frm) + 1 if frm else 0


def get_logs(filters):
    """Workshop / Idle periods, grouped by vehicle."""
    if not frappe.db.table_exists(LOG):
        return {}
    conds = [[LOG, "parenttype", "=", "Vehicle"]]
    if filters.get("vehicle"):
        conds.append([LOG, "parent", "=", filters.vehicle])
    if filters.get("from_date"):
        conds.append([LOG, "from_date", ">=", filters.from_date])
    if filters.get("to_date"):
        conds.append([LOG, "from_date", "<=", filters.to_date])

    rows = frappe.get_all(
        LOG,
        filters=conds,
        fields=["parent", "status", "from_date", "to_date", "workshop_name", "reason", "creation"],
        parent_doctype="Vehicle",
        limit_page_length=0,
    )
    out = {}
    for r in rows:
        out.setdefault(r.parent, []).append(r)
    return out


def get_data(filters):
    conds = [["Vehicle Deployment", "docstatus", "<", 2]]
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

    by_vehicle = {}
    for d in deps:
        if d.vehicle:
            by_vehicle.setdefault(d.vehicle, []).append(d)

    logs_by_vehicle = get_logs(filters)

    # vehicles that were only ever in the workshop / idle (never deployed) also belong in the report,
    # unless the user is filtering by customer or driver
    vehicles = set(by_vehicle)
    if not filters.get("customer") and not filters.get("driver_name"):
        vehicles |= set(logs_by_vehicle)

    info = {}
    if vehicles:
        for v in frappe.get_all(
            "Vehicle",
            filters={"name": ["in", list(vehicles)]},
            fields=["name", VEHICLE_TYPE_FIELD, "make"],
            limit_page_length=0,
        ):
            info[v.name] = v

    rows = []
    for vehicle in sorted(vehicles):
        items = sorted(
            by_vehicle.get(vehicle, []), key=lambda d: (str(d.mobilization_date or ""), str(d.creation))
        )
        logs = sorted(logs_by_vehicle.get(vehicle, []), key=lambda l: (str(l.from_date or ""), str(l.creation)))

        current = next((d for d in reversed(items) if d.status == "Mobilized"), None)
        open_log = next((l for l in reversed(logs) if not l.to_date), None)
        ended = [d.actual_end_date for d in items if d.actual_end_date]

        days = sum(_days(d.mobilization_date, d.actual_end_date) for d in items)
        workshop_days = sum(_days(l.from_date, l.to_date) for l in logs if l.status == "Workshop")
        idle_days = sum(_days(l.from_date, l.to_date) for l in logs if l.status == "Idle")

        if current:
            now, since, note = "On Deployment", current.mobilization_date, ""
        elif open_log:
            now, since = open_log.status, open_log.from_date
            note = " - ".join(x for x in (open_log.workshop_name, open_log.reason) if x)
        else:
            now, since, note = "Free", None, ""

        v = info.get(vehicle) or {}
        rows.append({
            "vehicle": vehicle,
            "vehicle_type": v.get(VEHICLE_TYPE_FIELD) or "",
            "make": v.get("make") or "",
            "current_status": now,
            "current_driver": (current.driver_name or current.driver) if current else "",
            "current_customer": current.customer if current else "",
            "current_site": current.site if current else "",
            "current_site_location": current.site_location if current else "",
            "since": since,
            "current_note": note,
            "total_deployments": len(items),
            "driver_count": len({d.driver_name or d.driver for d in items if d.driver_name or d.driver}),
            "client_count": len({d.customer for d in items if d.customer}),
            "total_days": days,
            "workshop_days": workshop_days,
            "idle_days": idle_days,
            "last_demobilized": max(ended) if ended else None,
        })

    if filters.get("current_status"):
        rows = [r for r in rows if r["current_status"] == filters.current_status]
    return rows


def get_summary(data):
    if not data:
        return []

    def n(status):
        return len([r for r in data if r["current_status"] == status])

    return [
        {"value": len(data), "label": _("Vehicles"), "datatype": "Int"},
        {"value": n("On Deployment"), "label": _("On Deployment"), "datatype": "Int", "indicator": "Green"},
        {"value": n("Workshop"), "label": _("In Workshop"), "datatype": "Int", "indicator": "Red"},
        {"value": n("Idle"), "label": _("Idle"), "datatype": "Int", "indicator": "Orange"},
        {"value": n("Free"), "label": _("Free"), "datatype": "Int", "indicator": "Blue"},
    ]