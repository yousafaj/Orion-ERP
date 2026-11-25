
import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today

# =====================================================================
# SETTINGS: check these against your system
# =====================================================================

# Vehicle fields
VEHICLE_STATUS_FIELD = "custom_status"
VEHICLE_OK_STATUS = ["Active"]
VEHICLE_STATE_FIELD = "custom_state"
VEHICLE_CUSTOMER_FIELD = "custom_current_customer"
VEHICLE_PROJECT_FIELD = "custom_project"      # a Link to Project; filled only if the order's site text is an existing Project
VEHICLE_TYPE_FIELD = "custom_vehicle_type"
STATE_WITH_CLIENT = "With Client"
STATE_FREE = "Available"                      # MUST be an option of the Vehicle State field

# Which employees are drivers (Employee > Designation). Use [] to accept every employee.
DRIVER_DESIGNATIONS = ["Driver"]
CERT_TABLE = "custom_vehicle_certifications"
CERT_NAME_FIELD = "certification_name"
CERT_EXPIRY_FIELD = "date_of_expiry"
# Certificate table inside Vehicle
CERT_MUST_BE_VALID = ["registration", "insurance"]   # [] = check all certificates

BUSY = ("Mobilized",)                         # deployment statuses that mean "busy"
ALERT_ROLE = "Fleet Manager"
# ALERT_DAYS = (30, 7)
ALERT_DAYS = (2,)        # alert 2 days before expiry. Use (2, 1, 0) to also alert the next day and on the expiry day


# =====================================================================
# HELPERS
# =====================================================================

def _driver_key(driver):
    """A driver (Pre-Employment Training) is identified by its Employee."""
    if not driver:
        return driver
    return frappe.db.get_value("Pre-Employment Training", driver, "employee_id") or driver


def _driver_name(driver):
    emp = _driver_key(driver)
    return frappe.db.get_value("Employee", emp, "employee_name") if emp else None


def _busy(field):
    """{vehicle or driver-key: deployment} for everything currently deployed."""
    rows = frappe.get_all(
        "Vehicle Deployment",
        filters={"docstatus": ["<", 2], "status": ["in", list(BUSY)]},
        fields=["name", "vehicle", "driver", "mobilization_order", "site"],
        limit_page_length=0,
    )
    out = {}
    for r in rows:
        key = _driver_key(r.driver) if field == "driver" else r.vehicle
        out[key] = r
    return out


def _vehicle_expired_certs(vehicle):
    doc = frappe.get_doc("Vehicle", vehicle)
    expired = []
    for row in doc.get(CERT_TABLE) or []:
        name = (row.get(CERT_NAME_FIELD) or "").strip()
        expiry = row.get(CERT_EXPIRY_FIELD)
        if not expiry:
            continue
        if CERT_MUST_BE_VALID and not any(k.lower() in name.lower() for k in CERT_MUST_BE_VALID):
            continue
        if getdate(expiry) < getdate(today()):
            expired.append(f"{name} (expired {expiry})")
    return expired


def _check_vehicle(vehicle, busy_vehicles, label=""):

    if frappe.db.get_value("Vehicle", vehicle, VEHICLE_STATE_FIELD) == "Workshop":
        frappe.throw(_("{0}Vehicle {1} is in the workshop and cannot be assigned.").format(label, vehicle))
    if vehicle in busy_vehicles:
        b = busy_vehicles[vehicle]
        frappe.throw(_("{0}Vehicle {1} is already deployed ({2}, site {3}).").format(label, vehicle, b.name, b.site or "-"))
    if VEHICLE_STATUS_FIELD:
        status = frappe.db.get_value("Vehicle", vehicle, VEHICLE_STATUS_FIELD)
        if status not in VEHICLE_OK_STATUS:
            frappe.throw(_("{0}Vehicle {1} has status '{2}' and cannot be assigned.").format(label, vehicle, status))
    expired = _vehicle_expired_certs(vehicle)
    if expired:
        frappe.throw(_("{0}Vehicle {1} has expired documents: {2}").format(label, vehicle, ", ".join(expired)))


def _check_driver(driver, busy_drivers, label=""):
    key = _driver_key(driver)
    if key in busy_drivers:
        b = busy_drivers[key]
        frappe.throw(_("{0}Driver {1} is already deployed ({2}, site {3}).").format(label, _driver_name(driver) or driver, b.name, b.site or "-"))
    # TODO: driving license check (needs the certificate table of Pre-Employment Training)


def _vehicle_with_client(vehicle, customer, site):
    values = {
        VEHICLE_STATE_FIELD: STATE_WITH_CLIENT,
        VEHICLE_CUSTOMER_FIELD: customer,
        VEHICLE_PROJECT_FIELD: site if site and frappe.db.exists("Project", site) else None,
    }
    frappe.db.set_value("Vehicle", vehicle, values)


def _vehicle_free(vehicle):
    frappe.db.set_value(
        "Vehicle", vehicle,
        {VEHICLE_STATE_FIELD: STATE_FREE, VEHICLE_CUSTOMER_FIELD: None, VEHICLE_PROJECT_FIELD: None},
    )


def _make_deployment(order, vehicle, driver, start_date, sub_location=None, replacement_of=None, reason=None):
    meta = frappe.get_meta("Vehicle Deployment")
    dep = frappe.new_doc("Vehicle Deployment")
    dep.mobilization_order = order.name
    dep.customer = order.customer
    dep.site = order.project
    dep.site_location = order.site_location
    dep.sub_location = sub_location
    dep.vehicle = vehicle
    dep.vehicle_type = frappe.db.get_value("Vehicle", vehicle, VEHICLE_TYPE_FIELD)
    dep.driver = driver
    dep.driver_name = _driver_name(driver)
    dep.mobilization_date = start_date
    dep.expected_end_date = order.expected_end_date
    dep.status = "Mobilized"
    if replacement_of:
        dep.replacement_of = replacement_of
        dep.replacement_reason = reason
    dep.insert()
    if meta.is_submittable:
        dep.submit()
    _vehicle_with_client(vehicle, order.customer, order.project)
    close_status_period(vehicle, start_date)
    return dep


# def _close_deployment(name, end_reason, reason=None):
#     """Closes a deployment: status becomes Demobilized, and end_reason says why it ended
#     (Driver Replaced / Vehicle Replaced / Job Completed)."""
#     values = {"status": "Demobilized", "actual_end_date": today()}
#     meta = frappe.get_meta("Vehicle Deployment")
#     for fieldname in ("end_reason", "ended_because"):  # works with either fieldname
#         if meta.has_field(fieldname):
#             values[fieldname] = end_reason
#             break
#     if reason:
#         values["replacement_reason"] = reason
#     frappe.db.set_value("Vehicle Deployment", name, values)

def _close_deployment(name, end_reason, reason=None, end_date=None):
    values = {"status": "Demobilized", "actual_end_date": end_date or today()}
    meta = frappe.get_meta("Vehicle Deployment")
    for fieldname in ("end_reason", "ended_because"):
        if meta.has_field(fieldname):
            values[fieldname] = end_reason
            break
    if reason:
        values["replacement_reason"] = reason
    frappe.db.set_value("Vehicle Deployment", name, values)

def _update_totals(order_name):
    rows = frappe.get_all("Mobilization Order Vehicle", filters={"parent": order_name}, fields=["status"])
    frappe.db.set_value(
        "Mobilization Order", order_name,
        {"total_assigned": len(rows), "total_mobilized": len([r for r in rows if r.status == "Mobilized"])},
        update_modified=False,
    )


def _get_order_row(order, row_name):
    row = next((r for r in order.vehicles if r.name == row_name), None)
    if not row:
        frappe.throw(_("Row not found."))
    if row.status != "Mobilized" or not row.deployment:
        frappe.throw(_("Only a Mobilized row can be replaced."))
    return row


# =====================================================================
# VALIDATION (called from mobilization_order.py)
# =====================================================================

def validate_order(doc, method=None):
    rows = [r for r in (doc.get("vehicles") or []) if r.status != "Demobilized"]
    if not rows:
        frappe.throw(_("Add at least one vehicle row."))

    busy_v = {k: v for k, v in _busy("vehicle").items() if v.mobilization_order != doc.name}
    busy_d = {k: v for k, v in _busy("driver").items() if v.mobilization_order != doc.name}

    seen_v, seen_d = set(), set()
    for r in rows:
        label = _("Row {0}: ").format(r.idx)
        if not r.vehicle:
            frappe.throw(label + _("Vehicle is required."))
        if not r.driver:
            frappe.throw(label + _("Please select a driver."))

        key = _driver_key(r.driver)
        if r.vehicle in seen_v:
            frappe.throw(label + _("Vehicle {0} appears twice in this order.").format(r.vehicle))
        if key in seen_d:
            frappe.throw(label + _("This driver appears twice in this order."))
        seen_v.add(r.vehicle)
        seen_d.add(key)

        # keep the display fields correct
        r.vehicle_type = frappe.db.get_value("Vehicle", r.vehicle, VEHICLE_TYPE_FIELD)
        r.driver_name = _driver_name(r.driver)

        if not r.deployment:  # already mobilized rows were checked when created
            _check_vehicle(r.vehicle, busy_v, label)
            _check_driver(r.driver, busy_d, label)

    if doc.vehicles_required and len(rows) > doc.vehicles_required:
        frappe.msgprint(
            _("You assigned {0} vehicles but the client requires {1}.").format(len(rows), doc.vehicles_required),
            indicator="orange",
        )

    doc.total_assigned = len(doc.get("vehicles") or [])
    doc.total_mobilized = len([r for r in doc.get("vehicles") or [] if r.status == "Mobilized"])


# =====================================================================
# LISTS FOR THE BUTTONS  (return [{value, label}])
# =====================================================================

@frappe.whitelist()
def get_vehicle_history(vehicle):
    """Everything about one vehicle for the popup of the Vehicle Movement Report:
    deployments AND workshop / idle periods in one timeline."""
    frappe.has_permission("Vehicle Deployment", "read", throw=True)

    v = frappe.db.get_value(
        "Vehicle", vehicle,
        ["name", "make", "model", "chassis_no", "last_odometer", "fuel_type",
         VEHICLE_TYPE_FIELD, VEHICLE_STATUS_FIELD, VEHICLE_STATE_FIELD],
        as_dict=True,
    ) or frappe._dict(name=vehicle)

    # ---------- deployments ----------
    meta = frappe.get_meta("Vehicle Deployment")
    end_fn = next((f for f in ("end_reason", "ended_because") if meta.has_field(f)), None)
    fields = [
        "name", "driver", "driver_name", "customer", "site", "site_location", "sub_location",
        "mobilization_date", "actual_end_date", "status", "replacement_reason",
        "mobilization_order", "replaced_by", "replacement_of", "creation",
    ]
    if end_fn:
        fields.append(f"{end_fn} as end_reason")

    deployments = frappe.get_all(
        "Vehicle Deployment",
        filters={"vehicle": vehicle, "docstatus": ["<", 2]},
        fields=fields,
        limit_page_length=0,
    )
    for r in deployments:
        r.kind = "deployment"
        r.start = r.mobilization_date
        r.days = (date_diff(r.actual_end_date or today(), r.mobilization_date) + 1) if r.mobilization_date else None
        if not r.get("end_reason") and r.status in ("Replaced", "Driver Replaced", "Vehicle Replaced"):
            r.end_reason = r.status

    # ---------- workshop / idle periods ----------
    logs = []
    if frappe.db.table_exists(LOG):
        logs = frappe.get_all(
            LOG,
            filters={"parent": vehicle, "parenttype": "Vehicle"},
            fields=["name", "status", "from_date", "to_date", "workshop_name", "reason", "source_order", "creation"],
            parent_doctype="Vehicle",
            limit_page_length=0,
        )
    for l in logs:
        l.kind = l.status                      # "Workshop" or "Idle"
        l.start = l.from_date
        l.open = not l.to_date
        l.days = (date_diff(l.to_date or today(), l.from_date) + 1) if l.from_date else None

    # ---------- one timeline, newest first ----------
    history = deployments + logs
    history.sort(key=lambda r: (str(r.start or ""), str(r.creation)), reverse=True)

    # ---------- where is the vehicle now ----------
    current = next((r for r in deployments if r.status == "Mobilized"), None)
    open_log = next((l for l in sorted(logs, key=lambda x: (str(x.from_date), str(x.creation)), reverse=True) if l.open), None)
    if current:
        now = {"kind": "On Deployment"}
    elif open_log:
        now = {
            "kind": open_log.status,
            "since": open_log.from_date,
            "days": open_log.days,
            "workshop_name": open_log.workshop_name,
            "reason": open_log.reason,
        }
    else:
        now = {"kind": "Free"}

    def total(status):
        return sum(l.days or 0 for l in logs if l.status == status)

    return {
        "vehicle": {
            "name": v.get("name"),
            "vehicle_type": v.get(VEHICLE_TYPE_FIELD),
            "make": v.get("make"),
            "model": v.get("model"),
            "chassis_no": v.get("chassis_no"),
            "status": v.get(VEHICLE_STATUS_FIELD),
            "state": v.get(VEHICLE_STATE_FIELD),
            "odometer": v.get("last_odometer"),
            "fuel_type": v.get("fuel_type"),
        },
        "now": now,
        "current": current,
        "summary": {
            "deployments": len(deployments),
            "drivers": len({r.driver_name or r.driver for r in deployments if r.driver_name or r.driver}),
            "clients": len({r.customer for r in deployments if r.customer}),
            "total_days": sum(r.days or 0 for r in deployments),
            "workshop_days": total("Workshop"),
            "workshop_times": len([l for l in logs if l.status == "Workshop"]),
            "idle_days": total("Idle"),
        },
        "history": history,
    }



# @frappe.whitelist()
# def get_vehicle_history(vehicle):
#     """Everything about one vehicle for the popup of the Vehicle Movement Report."""
#     frappe.has_permission("Vehicle Deployment", "read", throw=True)

#     v = frappe.db.get_value(
#         "Vehicle", vehicle,
#         ["name", "make", "model", "chassis_no", "last_odometer", "fuel_type",
#          VEHICLE_TYPE_FIELD, VEHICLE_STATUS_FIELD, VEHICLE_STATE_FIELD],
#         as_dict=True,
#     ) or frappe._dict(name=vehicle)

#     meta = frappe.get_meta("Vehicle Deployment")
#     end_fn = next((f for f in ("end_reason", "ended_because") if meta.has_field(f)), None)
#     fields = [
#         "name", "driver", "driver_name", "customer", "site", "site_location", "sub_location",
#         "mobilization_date", "actual_end_date", "status", "replacement_reason",
#         "mobilization_order", "replaced_by", "replacement_of", "creation",
#     ]
#     if end_fn:
#         fields.append(f"{end_fn} as end_reason")

#     rows = frappe.get_all(
#         "Vehicle Deployment",
#         filters={"vehicle": vehicle, "docstatus": ["<", 2]},
#         fields=fields,
#         limit_page_length=0,
#     )
#     rows.sort(key=lambda r: (str(r.mobilization_date or ""), str(r.creation)), reverse=True)

#     for r in rows:
#         r.days = (date_diff(r.actual_end_date or today(), r.mobilization_date) + 1) if r.mobilization_date else None
#         if not r.get("end_reason") and r.status in ("Replaced", "Driver Replaced", "Vehicle Replaced"):
#             r.end_reason = r.status

#     current = next((r for r in rows if r.status == "Mobilized"), None)
#     return {
#         "vehicle": {
#             "name": v.get("name"),
#             "vehicle_type": v.get(VEHICLE_TYPE_FIELD),
#             "make": v.get("make"),
#             "model": v.get("model"),
#             "chassis_no": v.get("chassis_no"),
#             "status": v.get(VEHICLE_STATUS_FIELD),
#             "state": v.get(VEHICLE_STATE_FIELD),
#             "odometer": v.get("last_odometer"),
#             "fuel_type": v.get("fuel_type"),
#         },
#         "current": current,
#         "summary": {
#             "deployments": len(rows),
#             "drivers": len({r.driver_name or r.driver for r in rows if r.driver_name or r.driver}),
#             "clients": len({r.customer for r in rows if r.customer}),
#             "total_days": sum(r.days or 0 for r in rows),
#         },
#         "history": rows,
#     }


@frappe.whitelist()
def get_driver_name(driver):
    """Used by the form to show the driver's name as soon as a driver is picked."""
    return _driver_name(driver) or driver


@frappe.whitelist()
def get_free_vehicles():
    busy = _busy("vehicle")
    filters = {}
    if VEHICLE_STATUS_FIELD:
        filters[VEHICLE_STATUS_FIELD] = ["in", VEHICLE_OK_STATUS]
    rows = frappe.get_all("Vehicle", filters=filters,
        fields=["name", VEHICLE_TYPE_FIELD, "make", VEHICLE_STATE_FIELD], limit_page_length=0)
    out = []
    for v in rows:
        if v.name in busy or v.get(VEHICLE_STATE_FIELD) == "Workshop":
            continue
        out.append({"value": v.name, "label": f"{v.name}  |  {v.get(VEHICLE_TYPE_FIELD) or '-'}  |  {v.make or ''}"})
    return out


@frappe.whitelist()
def get_free_drivers():
    # Every Pre-Employment Training record is a driver.
    busy = _busy("driver")
    pets = frappe.get_all(
        "Pre-Employment Training",
        filters={"docstatus": ["<", 2]},
        fields=["name", "employee_id"],
        limit_page_length=0,
    )
    ids = [p.employee_id for p in pets if p.employee_id]
    names = {}
    if ids:
        names = {
            e.name: e.employee_name
            for e in frappe.get_all("Employee", filters={"name": ["in", ids]}, fields=["name", "employee_name"], limit_page_length=0)
        }
    out, seen = [], set()
    for p in pets:
        key = p.employee_id or p.name  # same rule as _driver_key
        if key in busy or key in seen:
            continue
        seen.add(key)
        who = names.get(p.employee_id) or p.name
        out.append({"value": p.name, "label": f"{who}  |  {p.employee_id or '-'}  |  {p.name}"})
    return out


# =====================================================================
# BUTTON ACTIONS
# =====================================================================

@frappe.whitelist()
def create_deployments(order):
    doc = frappe.get_doc("Mobilization Order", order)
    doc.check_permission("write")
    if doc.docstatus != 1:
        frappe.throw(_("Submit/approve the order first."))

    busy_v = _busy("vehicle")
    busy_d = _busy("driver")
    created = 0
    for r in doc.vehicles:
        if r.deployment:
            continue
        label = _("Row {0}: ").format(r.idx)
        _check_vehicle(r.vehicle, busy_v, label)
        _check_driver(r.driver, busy_d, label)
        dep = _make_deployment(
            doc, r.vehicle, r.driver, r.mobilization_date or doc.planned_mobilization_date, r.sub_location
        )
        frappe.db.set_value("Mobilization Order Vehicle", r.name, {"deployment": dep.name, "status": "Mobilized"})
        busy_v[r.vehicle] = frappe._dict(name=dep.name, site=doc.project)
        busy_d[_driver_key(r.driver)] = frappe._dict(name=dep.name, site=doc.project)
        created += 1

    _update_totals(order)
    return created


@frappe.whitelist()
def replace_driver(order, row_name, new_driver, reason):
    doc = frappe.get_doc("Mobilization Order", order)
    doc.check_permission("write")
    row = _get_order_row(doc, row_name)
    if not reason:
        frappe.throw(_("Reason is required."))
    _check_driver(new_driver, _busy("driver"))

    old = row.deployment
    _close_deployment(old, "Driver Replaced", reason)
    new = _make_deployment(doc, row.vehicle, new_driver, today(), row.sub_location, replacement_of=old, reason=reason)
    frappe.db.set_value("Vehicle Deployment", old, "replaced_by", new.name)
    frappe.db.set_value(
        "Mobilization Order Vehicle", row.name,
        {"driver": new_driver, "driver_name": _driver_name(new_driver), "deployment": new.name, "status": "Mobilized"},
    )
    _update_totals(order)
    return new.name


@frappe.whitelist()
def replace_vehicle(order, row_name, new_vehicle, reason):
    doc = frappe.get_doc("Mobilization Order", order)
    doc.check_permission("write")
    row = _get_order_row(doc, row_name)
    if not reason:
        frappe.throw(_("Reason is required."))
    _check_vehicle(new_vehicle, _busy("vehicle"))

    old = row.deployment
    old_vehicle = row.vehicle
    _close_deployment(old, "Vehicle Replaced", reason)
    _vehicle_free(old_vehicle)
    new = _make_deployment(doc, new_vehicle, row.driver, today(), row.sub_location, replacement_of=old, reason=reason)
    frappe.db.set_value("Vehicle Deployment", old, "replaced_by", new.name)
    frappe.db.set_value(
        "Mobilization Order Vehicle", row.name,
        {
            "vehicle": new_vehicle,
            "vehicle_type": frappe.db.get_value("Vehicle", new_vehicle, VEHICLE_TYPE_FIELD),
            "deployment": new.name,
            "status": "Mobilized",
        },
    )
    _update_totals(order)
    return new.name




# @frappe.whitelist()
# def demobilize_order(order, moves=None):
#     """moves = JSON list: [{row_name, goes_to (Available/Idle/Workshop), reason, workshop_name}]"""
#     doc = frappe.get_doc("Mobilization Order", order)
#     doc.check_permission("write")
#     if doc.docstatus != 1:
#         frappe.throw(_("Only a submitted order can be demobilized."))

#     moves = {m.get("row_name"): m for m in (frappe.parse_json(moves) or [])}
#     rows = [r for r in doc.vehicles if r.status == "Mobilized" and r.deployment]

#     # check everything first, so nothing is half done
#     for r in rows:
#         m = moves.get(r.name) or {}
#         if (m.get("goes_to") or STATE_FREE) == "Workshop" and not (m.get("reason") or "").strip():
#             frappe.throw(_("Vehicle {0}: enter the reason for the workshop.").format(r.vehicle))

#     count = 0
#     for r in rows:
#         m = moves.get(r.name) or {}
#         goes = m.get("goes_to") or STATE_FREE
#         _close_deployment(r.deployment, "Job Completed")
#         if goes in ("Idle", "Workshop"):
#             open_status_period(r.vehicle, goes, today(), m.get("reason"), m.get("workshop_name"), order)
#         else:
#             _vehicle_free(r.vehicle)
#         frappe.db.set_value("Mobilization Order Vehicle", r.name, "status", "Demobilized")
#         count += 1
#     _update_totals(order)
#     return count




# =====================================================================
# DAILY EXPIRY EMAIL (already registered in your hooks.py)
# =====================================================================

# def send_expiry_alerts():
#     lines = []
#     for vehicle in frappe.get_all("Vehicle", pluck="name", limit_page_length=0):
#         doc = frappe.get_doc("Vehicle", vehicle)
#         for row in doc.get(CERT_TABLE) or []:
#             expiry = row.get(CERT_EXPIRY_FIELD)
#             if not expiry:
#                 continue
#             days = date_diff(expiry, today())
#             if days in ALERT_DAYS:
#                 lines.append(f"Vehicle {vehicle}: {row.get(CERT_NAME_FIELD)} expires on {expiry} ({days} days)")
#     if not lines:
#         return

#     users = frappe.get_all("Has Role", filters={"role": ALERT_ROLE, "parenttype": "User"}, pluck="parent")
#     recipients = [
#         u for u in set(users)
#         if u not in ("Administrator", "Guest") and frappe.db.get_value("User", u, "enabled")
#     ]
#     if not recipients:
#         return
#     frappe.sendmail(recipients=recipients, subject=_("Fleet documents expiring soon"), message="<br>".join(lines))


def send_expiry_alerts():
    alerts = []
    for vehicle in frappe.get_all("Vehicle", pluck="name", limit_page_length=0):
        doc = frappe.get_doc("Vehicle", vehicle)
        for row in doc.get(CERT_TABLE) or []:
            expiry = row.get(CERT_EXPIRY_FIELD)
            if not expiry:
                continue
            days = date_diff(expiry, today())
            if days in ALERT_DAYS:
                alerts.append((
                    vehicle,
                    f"Vehicle {vehicle}: {row.get(CERT_NAME_FIELD)} expires on {expiry} ({days} day(s) left). Please renew it.",
                ))
    if not alerts:
        return

    users = frappe.get_all("Has Role", filters={"role": ALERT_ROLE, "parenttype": "User"}, pluck="parent")
    recipients = [
        u for u in set(users)
        if u not in ("Administrator", "Guest") and frappe.db.get_value("User", u, "enabled")
    ]
    if not recipients:
        return

    # bell notification in the app
    for vehicle, msg in alerts:
        for user in recipients:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": msg,
                "for_user": user,
                "type": "Alert",
                "document_type": "Vehicle",
                "document_name": vehicle,
            }).insert(ignore_permissions=True)

    # email (works only if an Email Account is set up)
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=_("Vehicle certificates expiring soon"),
            message="<br>".join(m for _v, m in alerts),
        )
    except Exception:
        frappe.log_error(title="Vehicle expiry email failed")



# =====================================================================
# WORKSHOP / IDLE TRACKING
# Vehicle Status Log is a CHILD table of Vehicle (Vehicle > custom_status_log).
#
# In fleet_oprations.py:
#   1. DELETE the old  def demobilize_order(order, moves=None): ...  (the active one)
#   2. DELETE everything from the line "# APPEND this whole file at the bottom of:" to the end of the file
#   3. PASTE this whole file at the very bottom
# =====================================================================

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today

LOG = "Vehicle Status Log"
LOG_TABLE_FIELD = "custom_status_log"        # fieldname of the Table field you add on Vehicle
STATE_IDLE = "Idle"
STATE_WORKSHOP = "Workshop"
STATE_CHOICES = (STATE_FREE, STATE_IDLE, STATE_WORKSHOP)   # Available / Idle / Workshop
STATUS_FLEET_ROLES = ["Fleet Operator", "Fleet Manager", "System Manager"]


# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------

def _open_logs(vehicle):
    """Idle / Workshop periods of this vehicle that have no To Date yet."""
    if not frappe.db.table_exists(LOG):
        return []
    return frappe.get_all(
        LOG,
        filters={"parent": vehicle, "parenttype": "Vehicle", "to_date": ["is", "not set"]},
        fields=["name", "from_date", "status"],
        parent_doctype="Vehicle",
    )


def close_status_period(vehicle, on_date=None):
    """Ends the open Idle / Workshop period (if any)."""
    on_date = getdate(on_date or today())
    for log in _open_logs(vehicle):
        end = max(on_date, getdate(log.from_date))
        frappe.db.set_value(LOG, log.name, {"to_date": end, "days": date_diff(end, log.from_date)})


def open_status_period(vehicle, status, on_date=None, reason=None, workshop_name=None, order=None):
    """Closes the open period, starts a new Idle / Workshop period and sets the vehicle State."""
    on_date = getdate(on_date or today())
    close_status_period(vehicle, on_date)

    idx = frappe.db.count(LOG, {"parent": vehicle, "parenttype": "Vehicle"}) + 1
    log = frappe.get_doc(
        {
            "doctype": LOG,
            "parent": vehicle,
            "parenttype": "Vehicle",
            "parentfield": LOG_TABLE_FIELD,
            "idx": idx,
            "vehicle": vehicle,
            "status": status,
            "from_date": on_date,
            "reason": reason,
            "workshop_name": workshop_name,
            "source_order": order,
        }
    )
    log.insert(ignore_permissions=True)

    frappe.db.set_value(
        "Vehicle", vehicle,
        {VEHICLE_STATE_FIELD: status, VEHICLE_CUSTOMER_FIELD: None, VEHICLE_PROJECT_FIELD: None},
    )
    return log.name


def _validate_change(vehicle, goes, reason, mobilized=False):
    """Raises a clear message if this status change is not allowed."""
    if goes not in STATE_CHOICES:
        frappe.throw(_("Choose Available, Idle or Workshop."))
    if not mobilized:
        current = frappe.db.get_value("Vehicle", vehicle, VEHICLE_STATE_FIELD) or STATE_FREE
        if current == STATE_WITH_CLIENT:
            frappe.throw(_("Vehicle {0} is on a deployment. Demobilize it first.").format(vehicle))
        if current == goes:
            frappe.throw(_("Vehicle {0} is already {1}.").format(vehicle, goes))
    if goes == STATE_WORKSHOP and not (reason or "").strip():
        frappe.throw(_("Vehicle {0}: enter the reason for the workshop.").format(vehicle))


def _change_state(vehicle, goes, on_date=None, reason=None, workshop_name=None, order=None):
    """Moves a vehicle that is NOT on a deployment to Available / Idle / Workshop."""
    _validate_change(vehicle, goes, reason)
    if goes == STATE_FREE:
        close_status_period(vehicle, on_date)
        _vehicle_free(vehicle)
    else:
        open_status_period(vehicle, goes, on_date, reason, workshop_name, order)


# ---------------------------------------------------------------------
# used by the Mobilization Order popup
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_order_vehicle_states(order):
    """Every vehicle of the order with its current state (for the Demobilize popup)."""
    doc = frappe.get_doc("Mobilization Order", order)
    doc.check_permission("read")
    out = []
    for r in doc.vehicles:
        if not r.vehicle:
            continue
        mobilized = bool(r.status == "Mobilized" and r.deployment)
        if mobilized:
            state = STATE_WITH_CLIENT
        else:
            state = frappe.db.get_value("Vehicle", r.vehicle, VEHICLE_STATE_FIELD) or STATE_FREE
        out.append(
            {
                "row_name": r.name,
                "vehicle": r.vehicle,
                "driver_name": r.driver_name or r.driver or "",
                "state": state,
                "mobilized": mobilized,
                # now working for another job: cannot be changed from this order
                "locked": (not mobilized) and state == STATE_WITH_CLIENT,
            }
        )
    return out


# @frappe.whitelist()
# def demobilize_order(order, moves=None):
#     """moves = JSON list of the CHANGED rows:
#     [{row_name, goes_to (Available / Idle / Workshop), reason, workshop_name}]"""
#     doc = frappe.get_doc("Mobilization Order", order)
#     doc.check_permission("write")
#     if doc.docstatus != 1:
#         frappe.throw(_("Only a submitted order can be changed."))

#     moves = [m for m in (frappe.parse_json(moves) or []) if m.get("goes_to")]
#     if not moves:
#         frappe.throw(_("Nothing to change. Every vehicle already has this status."))

#     by_row = {r.name: r for r in doc.vehicles}

#     # 1) check everything first, so nothing is half done
#     plan = []
#     for m in moves:
#         r = by_row.get(m.get("row_name"))
#         if not r:
#             frappe.throw(_("Row not found."))
#         mobilized = bool(r.status == "Mobilized" and r.deployment)
#         _validate_change(r.vehicle, m["goes_to"], m.get("reason"), mobilized)
#         plan.append((r, m, mobilized))

#     # 2) apply
#     for r, m, mobilized in plan:
#         goes = m["goes_to"]
#         if mobilized:
#             _close_deployment(r.deployment, "Job Completed")
#             frappe.db.set_value("Mobilization Order Vehicle", r.name, "status", "Demobilized")
#             _vehicle_free(r.vehicle)
#             if goes != STATE_FREE:
#                 open_status_period(r.vehicle, goes, today(), m.get("reason"), m.get("workshop_name"), order)
#         else:
#             _change_state(r.vehicle, goes, today(), m.get("reason"), m.get("workshop_name"), order)

#     _update_totals(order)
#     return len(plan)


@frappe.whitelist()
def demobilize_order(order, moves=None):
    """moves = JSON list: [{row_name, goes_to, from_date, reason, workshop_name}]"""
    doc = frappe.get_doc("Mobilization Order", order)
    doc.check_permission("write")
    if doc.docstatus != 1:
        frappe.throw(_("Only a submitted order can be changed."))

    moves = [m for m in (frappe.parse_json(moves) or []) if m.get("goes_to")]
    if not moves:
        frappe.throw(_("Nothing to change. Every vehicle already has this status."))

    by_row = {r.name: r for r in doc.vehicles}

    plan = []
    for m in moves:
        r = by_row.get(m.get("row_name"))
        if not r:
            frappe.throw(_("Row not found."))
        if not m.get("from_date"):
            frappe.throw(_("Vehicle {0}: From Date is required.").format(r.vehicle))
        on = getdate(m["from_date"])
        if on > getdate(today()):
            frappe.throw(_("Vehicle {0}: the date cannot be in the future.").format(r.vehicle))
        mobilized = bool(r.status == "Mobilized" and r.deployment)
        if mobilized:
            start = frappe.db.get_value("Vehicle Deployment", r.deployment, "mobilization_date")
            if start and on < getdate(start):
                frappe.throw(_("Vehicle {0}: the date cannot be before the mobilization date {1}.").format(r.vehicle, start))
        _validate_change(r.vehicle, m["goes_to"], m.get("reason"), mobilized)
        plan.append((r, m, mobilized, on))

    for r, m, mobilized, on in plan:
        goes = m["goes_to"]
        if mobilized:
            _close_deployment(r.deployment, "Job Completed", end_date=on)
            frappe.db.set_value("Mobilization Order Vehicle", r.name, "status", "Demobilized")
            _vehicle_free(r.vehicle)
            if goes != STATE_FREE:
                open_status_period(r.vehicle, goes, on, m.get("reason"), m.get("workshop_name"), order)
        else:
            _change_state(r.vehicle, goes, on, m.get("reason"), m.get("workshop_name"), order)

    _update_totals(order)
    return len(plan)

# ---------------------------------------------------------------------
# used by the "Change Status" button on the Vehicle form
# ---------------------------------------------------------------------


@frappe.whitelist()
def change_vehicle_status(vehicle, to_status, on_date=None, reason=None, workshop_name=None):
    frappe.only_for(STATUS_FLEET_ROLES)
    on_date = getdate(on_date or today())
    if on_date > getdate(today()):
        frappe.throw(_("The date cannot be in the future."))
    _change_state(vehicle, to_status, on_date, reason, workshop_name)
    return True


@frappe.whitelist()
def get_status_history(vehicle):
    """Idle / Workshop history of one vehicle, newest first, with day totals."""
    frappe.has_permission("Vehicle", "read", throw=True)

    rows = frappe.get_all(
        LOG,
        filters={"parent": vehicle, "parenttype": "Vehicle"},
        fields=["name", "status", "from_date", "to_date", "workshop_name", "reason", "source_order"],
        order_by="from_date desc, creation desc",
        parent_doctype="Vehicle",
    )
    totals = {STATE_IDLE: 0, STATE_WORKSHOP: 0}
    for r in rows:
        r["open"] = not r.to_date
        r["days"] = date_diff(r.to_date or today(), r.from_date)  # always live
        totals[r.status] = totals.get(r.status, 0) + r["days"]

    return {"rows": rows, "idle_days": totals[STATE_IDLE], "workshop_days": totals[STATE_WORKSHOP]}


@frappe.whitelist()
def get_driver_history(driver):
    """Everything about one driver (all of his Pre-Employment Training records)
    for the popup of the Driver Movement Report."""
    frappe.has_permission("Vehicle Deployment", "read", throw=True)
 
    emp = frappe.db.get_value("Pre-Employment Training", driver, "employee_id")
    pets = (
        frappe.get_all("Pre-Employment Training", filters={"employee_id": emp}, pluck="name")
        if emp else [driver]
    )
 
    info = {}
    if emp:
        emeta = frappe.get_meta("Employee")
        wanted = [
            f for f in ("employee_name", "designation", "department", "company", "status", "cell_number")
            if emeta.has_field(f)
        ]
        info = frappe.db.get_value("Employee", emp, wanted, as_dict=True) or {}
 
    meta = frappe.get_meta("Vehicle Deployment")
    end_fn = next((f for f in ("end_reason", "ended_because") if meta.has_field(f)), None)
    fields = [
        "name", "vehicle", "vehicle_type", "driver", "driver_name", "customer", "site", "site_location",
        "sub_location", "mobilization_date", "actual_end_date", "status", "replacement_reason",
        "mobilization_order", "replaced_by", "replacement_of", "creation",
    ]
    if end_fn:
        fields.append(f"{end_fn} as end_reason")
 
    rows = frappe.get_all(
        "Vehicle Deployment",
        filters={"driver": ["in", pets], "docstatus": ["<", 2]},
        fields=fields,
        limit_page_length=0,
    )
 
    # who / which vehicle came before and after each deployment
    link_names = {r.replaced_by for r in rows if r.replaced_by} | {r.replacement_of for r in rows if r.replacement_of}
    nb = {}
    if link_names:
        nb = {
            x.name: x
            for x in frappe.get_all(
                "Vehicle Deployment",
                filters={"name": ["in", list(link_names)]},
                fields=["name", "driver_name", "vehicle"],
                limit_page_length=0,
            )
        }
 
    for r in rows:
        r.start = r.mobilization_date or getdate(r.creation)
        r.mobilization_date = r.start
        r.days = date_diff(r.actual_end_date or today(), r.start) + 1
        if not r.get("end_reason") and r.status in ("Replaced", "Driver Replaced", "Vehicle Replaced"):
            r.end_reason = r.status
        n, p = nb.get(r.replaced_by), nb.get(r.replacement_of)
        r.next_driver = n.driver_name if n else None
        r.next_vehicle = n.vehicle if n else None
        r.prev_driver = p.driver_name if p else None
        r.prev_vehicle = p.vehicle if p else None
 
    rows.sort(key=lambda r: (str(r.start), str(r.creation)), reverse=True)
    current = next((r for r in rows if r.status == "Mobilized"), None)
    name = info.get("employee_name") or next((r.driver_name for r in rows if r.driver_name), None) or driver
 
    return {
        "driver": {
            "name": name,
            "employee_id": emp,
            "designation": info.get("designation"),
            "department": info.get("department"),
            "company": info.get("company"),
            "status": info.get("status"),
            "mobile": info.get("cell_number"),
            "training_records": len(pets),
        },
        "current": current,
        "summary": {
            "deployments": len(rows),
            "vehicles": len({r.vehicle for r in rows if r.vehicle}),
            "clients": len({r.customer for r in rows if r.customer}),
            "total_days": sum(r.days or 0 for r in rows),
            "times_replaced": len([r for r in rows if r.get("end_reason") == "Driver Replaced"]),
        },
        "history": rows,
    }
 

@frappe.whitelist()
def swap_assignments(order, row_name, target_order, target_row_name, mode, reason):
    """Swaps between a Mobilized row of this order and a Mobilized row of another order
    (same customer, different site).
    mode = 'vehicle' : the two vehicles trade places, drivers stay
           'driver'  : the two drivers trade places, vehicles stay
           'both'    : vehicle and driver of the two rows trade places
    Both old deployments end and two new ones start today, linked to the old ones."""
    a = frappe.get_doc("Mobilization Order", order)
    b = frappe.get_doc("Mobilization Order", target_order)
    a.check_permission("write")
    b.check_permission("write")

    if mode not in ("vehicle", "driver", "both"):
        frappe.throw(_("Choose what to swap."))
    if not (reason or "").strip():
        frappe.throw(_("Reason is required."))
    if a.name == b.name:
        frappe.throw(_("Choose a different order."))
    if a.docstatus != 1 or b.docstatus != 1:
        frappe.throw(_("Both orders must be submitted."))
    if a.customer != b.customer:
        frappe.throw(_("Both orders must belong to the same customer."))
    if (a.project or "") == (b.project or ""):
        frappe.throw(_("Both orders are at the same site."))

    ra = _get_order_row(a, row_name)
    rb = _get_order_row(b, target_row_name)
    va, da = ra.vehicle, ra.driver
    vb, db = rb.vehicle, rb.driver

    if mode == "vehicle":
        na, nb = (vb, da), (va, db)
        end_reason = "Vehicle Replaced"
    elif mode == "driver":
        na, nb = (va, db), (vb, da)
        end_reason = "Driver Replaced"
    else:
        na, nb = (vb, db), (va, da)
        end_reason = "Site Changed"

    # check BEFORE changing anything
    if mode in ("vehicle", "both"):
        for v in (va, vb):
            expired = _vehicle_expired_certs(v)
            if expired:
                frappe.throw(_("Vehicle {0} has expired documents: {1}").format(v, ", ".join(expired)))

    old_a, old_b = ra.deployment, rb.deployment
    _close_deployment(old_a, end_reason, reason)
    _close_deployment(old_b, end_reason, reason)

    new_a = _make_deployment(a, na[0], na[1], today(), ra.sub_location, replacement_of=old_a, reason=reason)
    new_b = _make_deployment(b, nb[0], nb[1], today(), rb.sub_location, replacement_of=old_b, reason=reason)
    frappe.db.set_value("Vehicle Deployment", old_a, "replaced_by", new_a.name)
    frappe.db.set_value("Vehicle Deployment", old_b, "replaced_by", new_b.name)

    for row, (veh, drv), dep in ((ra, na, new_a), (rb, nb, new_b)):
        frappe.db.set_value(
            "Mobilization Order Vehicle", row.name,
            {
                "vehicle": veh,
                "vehicle_type": frappe.db.get_value("Vehicle", veh, VEHICLE_TYPE_FIELD),
                "driver": drv,
                "driver_name": _driver_name(drv),
                "deployment": dep.name,
                "status": "Mobilized",
            },
        )
    return True



@frappe.whitelist()
def get_orders_vehicle_states(orders):
    frappe.has_permission("Mobilization Order", "read", throw=True)
    orders = frappe.parse_json(orders) or []
    rows = frappe.get_all(
        "Mobilization Order Vehicle",
        filters={"parent": ["in", orders]},
        fields=["parent", "vehicle", "status", "deployment"],
        order_by="idx asc",
        limit_page_length=0,
    )
    out = {}
    for r in rows:
        if r.status == "Mobilized" and r.deployment:
            state = STATE_WITH_CLIENT
        elif r.status == "Demobilized":
            cur = frappe.db.get_value("Vehicle", r.vehicle, VEHICLE_STATE_FIELD)
            state = cur if cur in (STATE_IDLE, STATE_WORKSHOP) else "Demobilized"
        else:
            state = "Pending"
        out.setdefault(r.parent, []).append({"vehicle": r.vehicle, "state": state})
    return out