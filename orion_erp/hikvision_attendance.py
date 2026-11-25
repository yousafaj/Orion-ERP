"""
Hikvision -> ERPNext/HRMS Employee Checkin integration.

Rules: for each employee and shift window,
    first valid punch        -> one Employee Checkin, log type IN
    later valid punches      -> a single OUT checkin, moved to the latest punch
    everything else          -> not stored
"""

from collections import Counter
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import frappe
import requests
from frappe.utils import get_system_timezone
from requests.auth import HTTPDigestAuth

LOGGER_NAME = "hikvision_attendance"

VALID_MAJOR = 5
VALID_MINOR_CODES = {38, 75}  # 38 = fingerprint, 75 = face

# Punch closer than this to the IN is treated as a repeat of the IN.
MIN_MINUTES_BETWEEN_IN_AND_OUT = 30

OVERLAP_MINUTES = 30
MAX_BACKFILL_HOURS = 72
INITIAL_LOOKBACK_MINUTES = 60
UPDATE_SHIFT_LAST_SYNC = True

PAGE_SIZE = 30
REQUEST_TIMEOUT = 30


def get_device_configs():
    devices = []

    for name in ("office", "site"):
        url = frappe.conf.get(f"hikvision_{name}_url")
        username = frappe.conf.get(f"hikvision_{name}_username")
        password = frappe.conf.get(f"hikvision_{name}_password")

        if not any([url, username, password]):
            continue

        if not all([url, username, password]):
            frappe.throw(
                f"Incomplete Hikvision {name.title()} configuration. "
                "Configure its URL, username, and password."
            )

        log_type = frappe.conf.get(f"hikvision_{name}_log_type")
        if log_type not in (None, "IN", "OUT"):
            frappe.throw(f"hikvision_{name}_log_type must be 'IN' or 'OUT' if set.")

        devices.append({
            "name": name.title(),
            "url": url.rstrip("/"),
            "username": username,
            "password": password,
            "verify": frappe.conf.get(f"hikvision_{name}_verify_ssl", True),
            "log_type": log_type,
        })

    if not devices:
        frappe.throw("No Hikvision devices are configured.")

    return devices


def _tz():
    return ZoneInfo(get_system_timezone())


def fetch_device_events(device, start_time, end_time):
    url = f"{device['url']}/ISAPI/AccessControl/AcsEvent?format=json"
    auth = HTTPDigestAuth(device["username"], device["password"])

    all_events = []
    position = 0
    search_id = f"erpnext-{device['name'].lower()}-attendance"

    with requests.Session() as session:
        while True:
            payload = {
                "AcsEventCond": {
                    "searchID": search_id,
                    "searchResultPosition": position,
                    "maxResults": PAGE_SIZE,
                    "major": 0,
                    "minor": 0,
                    "startTime": start_time.isoformat(timespec="seconds"),
                    "endTime": end_time.isoformat(timespec="seconds"),
                }
            }

            response = session.post(
                url,
                json=payload,
                auth=auth,
                verify=device["verify"],
                timeout=REQUEST_TIMEOUT,
            )

            if not response.ok:
                frappe.throw(
                    f"Hikvision {device['name']} API error "
                    f"{response.status_code}: {response.text[:500]}"
                )

            event_info = response.json().get("AcsEvent", {})
            page_events = event_info.get("InfoList") or []
            all_events.extend(page_events)

            if not page_events or event_info.get("responseStatusStrg") != "MORE":
                break

            position += len(page_events)

    return all_events


def _cursor_key(device):
    return f"hikvision_last_sync_{device['name'].lower()}"


def get_sync_window(device):
    tz = _tz()
    end_time = datetime.now(tz)

    last = frappe.db.get_global(_cursor_key(device))
    if last:
        start_time = datetime.fromisoformat(last) - timedelta(minutes=OVERLAP_MINUTES)
        earliest = end_time - timedelta(hours=MAX_BACKFILL_HOURS)
        if start_time < earliest:
            start_time = earliest
            frappe.logger(LOGGER_NAME).warning(
                f"{device['name']}: cursor older than "
                f"{MAX_BACKFILL_HOURS}h, recovery capped."
            )
    else:
        start_time = end_time - timedelta(minutes=INITIAL_LOOKBACK_MINUTES)

    return start_time, end_time


def save_cursor(device, end_time):
    frappe.db.set_global(_cursor_key(device), end_time.isoformat())


def get_event_id(device_name, serial_no):
    return f"Hikvision {device_name}:{serial_no}"


def parse_event_time(text):
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is not None:
        dt = dt.astimezone(_tz()).replace(tzinfo=None)
    return dt


def get_shift_window(employee, timestamp):
    """(window_start, window_end, shift_type) from the employee's shift,
    including the Shift Type check-in/check-out margins. Falls back to the
    calendar day if there is no shift."""
    try:
        from hrms.hr.doctype.shift_assignment.shift_assignment import (
            get_actual_start_end_datetime_of_shift,
        )

        details = get_actual_start_end_datetime_of_shift(employee, timestamp, True)
        if details and details.get("actual_start") and details.get("actual_end"):
            shift_type = details.get("shift_type")
            if hasattr(shift_type, "name"):
                shift_type = shift_type.name
            return details["actual_start"], details["actual_end"], shift_type
    except Exception:
        frappe.logger(LOGGER_NAME).warning(
            f"Could not resolve shift for {employee}: {frappe.get_traceback()}"
        )

    day_start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    return day_start, day_start + timedelta(days=1) - timedelta(seconds=1), None


def load_window_state(employee, window_start, window_end):
    rows = frappe.get_all(
        "Employee Checkin",
        filters={"employee": employee, "time": ["between", [window_start, window_end]]},
        fields=["name", "time", "log_type", "attendance"],
        order_by="time asc",
    )

    return {
        "first": rows[0] if rows else None,
        "last": rows[-1] if len(rows) > 1 else None,
        "locked": any(r.get("attendance") for r in rows),
    }


def create_checkin(employee, timestamp, event_id, log_type):
    doc = frappe.new_doc("Employee Checkin")
    doc.employee = employee
    doc.time = timestamp
    doc.device_id = event_id
    doc.log_type = log_type
    doc.skip_auto_attendance = 0
    doc.insert(ignore_permissions=True)
    return doc


def move_checkin(name, timestamp, event_id, log_type):
    doc = frappe.get_doc("Employee Checkin", name)
    doc.time = timestamp
    doc.device_id = event_id
    doc.log_type = log_type
    doc.save(ignore_permissions=True)
    return doc


def process_device_events(device, events, dry_run=True):
    counters = Counter()
    seen_event_ids = set()
    states = {}

    events = sorted(
        events,
        key=lambda e: (e.get("time") or "", int(e.get("serialNo") or 0)),
    )

    for event in events:
        employee_number = str(event.get("employeeNoString") or "").strip()
        serial_no = event.get("serialNo")
        timestamp_text = event.get("time")

        if not employee_number or serial_no is None or not timestamp_text:
            counters["skipped"] += 1
            continue

        try:
            major = int(event.get("major", -1))
            minor = int(event.get("minor", -1))
        except (TypeError, ValueError):
            counters["skipped"] += 1
            continue

        if major != VALID_MAJOR or minor not in VALID_MINOR_CODES:
            counters["skipped"] += 1
            continue

        event_id = get_event_id(device["name"], serial_no)
        if event_id in seen_event_ids:
            counters["skipped"] += 1
            continue
        seen_event_ids.add(event_id)

        try:
            timestamp = parse_event_time(timestamp_text)
        except ValueError:
            counters["skipped"] += 1
            continue

        employee = frappe.db.get_value(
            "Employee", {"attendance_device_id": employee_number}, "name"
        )
        if not employee:
            frappe.logger(LOGGER_NAME).warning(
                f"Unmapped Hikvision employee number {employee_number} on "
                f"{device['name']}; event {serial_no} skipped."
            )
            counters["unmapped"] += 1
            counters["skipped"] += 1
            continue

        if frappe.db.exists("Employee Checkin", {"device_id": event_id}):
            counters["skipped"] += 1
            continue

        try:
            action, log_type, target = decide_action(device, employee, timestamp, states)
        except Exception:
            counters["errors"] += 1
            frappe.log_error(
                title=f"Hikvision {device['name']} shift lookup failed",
                message=f"event={event_id} employee={employee}\n\n"
                        f"{frappe.get_traceback()}",
            )
            continue

        if action == "skip":
            counters["skipped"] += 1
            continue

        if dry_run:
            print({
                "status": f"WOULD {action.upper()}",
                "employee": employee,
                "employee_device_id": employee_number,
                "time": str(timestamp),
                "log_type": log_type,
                "event_id": event_id,
            })
            counters["eligible"] += 1
            apply_to_state(states, target, action, log_type, timestamp, None)
            continue

        try:
            if action == "create":
                doc = create_checkin(employee, timestamp, event_id, log_type)
                counters["created"] += 1
            else:
                doc = move_checkin(target["name"], timestamp, event_id, log_type)
                counters["updated"] += 1
            counters["eligible"] += 1
            apply_to_state(states, target, action, log_type, timestamp, doc.name)
        except Exception:
            counters["errors"] += 1
            frappe.log_error(
                title=f"Hikvision {device['name']} checkin failed",
                message=f"event={event_id} employee={employee} "
                        f"time={timestamp}\n\n{frappe.get_traceback()}",
            )

    return {
        "eligible": counters["eligible"],
        "created": counters["created"],
        "updated": counters["updated"],
        "skipped": counters["skipped"],
        "unmapped": counters["unmapped"],
        "errors": counters["errors"],
        "dry_run": dry_run,
    }


def decide_action(device, employee, timestamp, states):
    """Return (action, log_type, target); action is create / update / skip."""

    if device["log_type"]:
        return "create", device["log_type"], {"key": None, "record": None}

    window_start, window_end, _shift = get_shift_window(employee, timestamp)
    key = (employee, window_start)

    if key not in states:
        states[key] = load_window_state(employee, window_start, window_end)
    state = states[key]

    if state["locked"]:
        return "skip", None, None

    first, last = state["first"], state["last"]

    if first is None:
        return "create", "IN", {"key": key, "record": None}

    if timestamp < first["time"]:
        return "update", "IN", {"key": key, "record": first, "name": first["name"]}

    if timestamp - first["time"] < timedelta(minutes=MIN_MINUTES_BETWEEN_IN_AND_OUT):
        return "skip", None, None

    if last is None:
        return "create", "OUT", {"key": key, "record": None}

    if timestamp > last["time"]:
        return "update", "OUT", {"key": key, "record": last, "name": last["name"]}

    return "skip", None, None


def apply_to_state(states, target, action, log_type, timestamp, name):
    key = target.get("key") if target else None
    if key is None or key not in states:
        return

    state = states[key]
    record = {
        "name": name or (target.get("record") or {}).get("name"),
        "time": timestamp,
        "log_type": log_type,
    }

    if log_type == "IN":
        state["first"] = record
    else:
        state["last"] = record


def preview_hikvision_attendance(minutes=30):
    end_time = datetime.now(_tz())
    start_time = end_time - timedelta(minutes=minutes)

    summary = {}
    for device in get_device_configs():
        try:
            events = fetch_device_events(device, start_time, end_time)
            result = process_device_events(device, events, dry_run=True)
            summary[device["name"]] = {"fetched": len(events), **result}
        except Exception as exc:
            summary[device["name"]] = {"error": str(exc)}

    print("Hikvision attendance preview:", summary)
    return summary


def sync_hikvision_attendance():
    summary = {}
    clean_end_times = []
    all_clean = True

    for device in get_device_configs():
        try:
            start_time, end_time = get_sync_window(device)
            events = fetch_device_events(device, start_time, end_time)
            result = process_device_events(device, events, dry_run=False)

            if result["errors"] == 0:
                save_cursor(device, end_time)
                clean_end_times.append(end_time)
            else:
                all_clean = False
            frappe.db.commit()

            summary[device["name"]] = {"fetched": len(events), **result}
        except Exception:
            all_clean = False
            frappe.db.rollback()
            frappe.log_error(
                title=f"Hikvision {device['name']} sync failed",
                message=frappe.get_traceback(),
            )
            summary[device["name"]] = {"error": "see Error Log"}

    if UPDATE_SHIFT_LAST_SYNC and all_clean and clean_end_times:
        synced_until = min(clean_end_times).astimezone(_tz()).replace(tzinfo=None)
        for shift in frappe.get_all(
            "Shift Type", filters={"enable_auto_attendance": 1}, pluck="name"
        ):
            frappe.db.set_value("Shift Type", shift, "last_sync_of_checkin", synced_until)
        frappe.db.commit()

    frappe.logger(LOGGER_NAME).info(f"Synchronization summary: {summary}")
    return summary


def inspect_hikvision_event_codes(minutes=30):
    end_time = datetime.now(_tz())
    start_time = end_time - timedelta(minutes=minutes)

    summary = {}

    for device in get_device_configs():
        try:
            events = fetch_device_events(device, start_time, end_time)

            counts = Counter()
            employee_events = []

            for event in events:
                major = event.get("major")
                minor = event.get("minor")
                counts[(str(major), str(minor))] += 1

                employee_no = event.get("employeeNoString") or event.get("employeeNo")
                if employee_no:
                    employee_events.append({
                        "employee_no": str(employee_no),
                        "major": major,
                        "minor": minor,
                        "time": event.get("time"),
                        "serial": event.get("serialNo"),
                    })

            summary[device["name"]] = {
                "total_events": len(events),
                "event_code_counts": [
                    {"major": ma, "minor": mi, "count": c}
                    for (ma, mi), c in sorted(counts.items())
                ],
                "employee_events": employee_events[-30:],
            }
        except Exception as exc:
            summary[device["name"]] = {"error": str(exc)}

    print(summary)
    return summary


# --------------------------------------------------------------------------
# Push endpoint: the device calls this URL for every event
# --------------------------------------------------------------------------

def _push_candidates():
    """JSON objects found in the request (form fields or raw body)."""
    import json

    found = []
    request = frappe.request

    for value in request.form.values():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                found.append(parsed)
        except (TypeError, ValueError):
            pass

    if not found:
        try:
            parsed = json.loads(request.get_data(as_text=True))
            if isinstance(parsed, dict):
                found.append(parsed)
        except (TypeError, ValueError):
            pass

    return found


def _normalize_push(data):
    """Convert a pushed AccessControllerEvent into the shape used by the
    pull sync. Returns None for events that are not access events."""
    event = data.get("AccessControllerEvent")
    if not isinstance(event, dict):
        return None

    return {
        "employeeNoString": event.get("employeeNoString") or event.get("employeeNo"),
        "serialNo": event.get("serialNo"),
        "major": event.get("majorEventType"),
        "minor": event.get("subEventType"),
        "time": data.get("dateTime"),
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def receive_push(device=None, token=None):
    """URL for the device:

    /api/method/orion_erp.integrations.hikvision_attendance.receive_push
        ?device=office&token=<hikvision_push_token>
    """
    import hmac

    expected = str(frappe.conf.get("hikvision_push_token") or "")
    if not expected or not hmac.compare_digest(str(token or ""), expected):
        frappe.throw("Not permitted", frappe.PermissionError)

    name = (device or "").strip().lower()
    if name not in ("office", "site"):
        frappe.throw("Unknown device")

    frappe.set_user("Administrator")

    candidates = _push_candidates()

    if frappe.conf.get("hikvision_push_debug"):
        frappe.log_error(
            title=f"Hikvision push raw ({name})",
            message=f"form keys: {list(frappe.request.form.keys())}\n"
                    f"files: {list(frappe.request.files.keys())}\n\n"
                    f"{str(candidates)[:4000]}",
        )

    events = [e for e in (_normalize_push(c) for c in candidates) if e]
    fresh = []
    for e in events:
        try:
            if getdate(parse_event_time(e["time"])) >= getdate(today()):
                fresh.append(e)
        except Exception:
            pass
    events = fresh

    if not events:
        return {"ok": True, "ignored": True}

    cfg = {
        "name": name.title(),
        "log_type": frappe.conf.get(f"hikvision_{name}_log_type"),
    }
    result = process_device_events(cfg, events, dry_run=False)
    return {"ok": True, **result}


def update_last_sync_of_checkin():
    from frappe.utils import now_datetime
    for shift in frappe.get_all("Shift Type", filters={"enable_auto_attendance": 1}, pluck="name"):
        frappe.db.set_value("Shift Type", shift, "last_sync_of_checkin", now_datetime())