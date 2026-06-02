"""Helpers for reading passport info from the Employee record.

Some organizations store passport details as a top-level field on Employee,
others store them as a row in a Certificates / Identifications child table
(e.g. row where Certification Name = "Passport No"). These helpers handle
both layouts by introspecting Employee meta at runtime — no hardcoded
child-table doctype name required.
"""

import frappe


# Heuristic keywords used to identify the right fields in any child table
# attached to Employee. Match is case-insensitive on label OR fieldname.
# Keep these specific enough to avoid false positives — e.g. "no" alone
# would match nominee_name, notice_period, monthly_no, etc.
_NAME_KEYWORDS = ("certification", "certificate", "document", "identification")
_REF_KEYWORDS = ("reference", "number")
_EXPIRY_KEYWORDS = ("expiry", "expir")
_PASSPORT_KEYWORDS = ("passport",)


def get_employee_passport_info(employee):
    """Return ``{"passport_number": str|None, "passport_expiry_date": date|None}``.

    Looks first at a top-level ``passport_number`` field on Employee, and
    falls back to scanning child tables for a "Passport No"-style row.
    """
    result = {"passport_number": None, "passport_expiry_date": None}
    if not employee:
        return result

    # Direct fields, if the org happens to have a top-level passport_number /
    # passport_expiry_date custom field.
    employee_meta = frappe.get_meta("Employee")
    direct_fields = []
    if employee_meta.has_field("passport_number"):
        direct_fields.append("passport_number")
    if employee_meta.has_field("passport_expiry_date"):
        direct_fields.append("passport_expiry_date")
    if direct_fields:
        row = frappe.db.get_value("Employee", employee, direct_fields, as_dict=True) or {}
        result["passport_number"] = row.get("passport_number")
        result["passport_expiry_date"] = row.get("passport_expiry_date")
        if result["passport_number"]:
            return result

    # Fallback: scan every child table on Employee for a row that looks like
    # a Passport entry.
    table = _resolve_passport_child_table(employee_meta)
    if not table:
        return result

    child_doctype = table["child_doctype"]
    name_field = table["name_field"]
    ref_field = table["ref_field"]
    expiry_field = table["expiry_field"]

    # All field/doctype names come from Frappe meta — they're vetted Python
    # identifiers, safe to interpolate. Only the employee value is user data,
    # and that's parameterized.
    select_cols = [f"`{ref_field}` AS passport_number"]
    if expiry_field:
        select_cols.append(f"`{expiry_field}` AS passport_expiry_date")

    query = (
        f"SELECT {', '.join(select_cols)} "
        f"FROM `tab{child_doctype}` "
        f"WHERE parent = %(emp)s "
        f"AND parenttype = 'Employee' "
        f"AND LOWER(`{name_field}`) LIKE %(needle)s "
        f"ORDER BY idx ASC LIMIT 1"
    )
    rows = frappe.db.sql(query, {"emp": employee, "needle": "%passport%"}, as_dict=True)
    if rows:
        result["passport_number"] = rows[0].get("passport_number") or result["passport_number"]
        if "passport_expiry_date" in rows[0]:
            result["passport_expiry_date"] = (
                rows[0].get("passport_expiry_date") or result["passport_expiry_date"]
            )
    return result


def find_expiring_passports(target_start, target_end):
    """Yield ``{"employee", "employee_name", "passport_number", "passport_expiry_date", "department"}``
    for active employees whose passport expires within the given date range.

    Uses the same child-table introspection as ``get_employee_passport_info``.
    """
    employee_meta = frappe.get_meta("Employee")

    # Path 1: top-level passport_expiry_date field exists.
    if employee_meta.has_field("passport_expiry_date") and employee_meta.has_field("passport_number"):
        yield from frappe.db.sql(
            """
            SELECT e.name AS employee, e.employee_name, e.passport_number,
                   e.passport_expiry_date, e.department
            FROM `tabEmployee` e
            WHERE e.passport_expiry_date BETWEEN %(start)s AND %(end)s
              AND e.status = 'Active'
            """,
            {"start": target_start, "end": target_end},
            as_dict=True,
        )
        return

    # Path 2: read from a child table on Employee.
    table = _resolve_passport_child_table(employee_meta)
    if not table or not table.get("expiry_field"):
        return

    child_doctype = table["child_doctype"]
    name_field = table["name_field"]
    ref_field = table["ref_field"]
    expiry_field = table["expiry_field"]

    query = (
        "SELECT e.name AS employee, e.employee_name, e.department, "
        f"ec.`{ref_field}` AS passport_number, "
        f"ec.`{expiry_field}` AS passport_expiry_date "
        f"FROM `tab{child_doctype}` ec "
        "INNER JOIN `tabEmployee` e ON e.name = ec.parent "
        f"WHERE LOWER(ec.`{name_field}`) LIKE %(needle)s "
        f"AND ec.`{expiry_field}` BETWEEN %(start)s AND %(end)s "
        "AND e.status = 'Active' "
        "AND ec.parenttype = 'Employee'"
    )
    yield from frappe.db.sql(
        query,
        {"needle": "%passport%", "start": target_start, "end": target_end},
        as_dict=True,
    )


def _resolve_passport_child_table(employee_meta):
    """Find the child table on Employee that holds passport-like rows.

    Returns a dict ``{"child_doctype", "name_field", "ref_field", "expiry_field"}``
    or ``None`` if no suitable child table exists.
    """
    for field in employee_meta.fields:
        if field.fieldtype != "Table" or not field.options:
            continue
        try:
            child_meta = frappe.get_meta(field.options)
        except Exception:
            continue

        name_field = _find_field(child_meta, _NAME_KEYWORDS)
        ref_field = _find_field(child_meta, _REF_KEYWORDS, exclude=("date",))
        expiry_field = _find_field(child_meta, _EXPIRY_KEYWORDS)
        if name_field and ref_field:
            return {
                "child_doctype": field.options,
                "name_field": name_field,
                "ref_field": ref_field,
                "expiry_field": expiry_field,
            }
    return None


def _find_field(meta, keywords, exclude=()):
    """Return the fieldname of the first field whose label or fieldname
    contains any of ``keywords`` (case-insensitive) and none of ``exclude``.
    """
    for f in meta.fields:
        haystack = f"{(f.label or '').lower()} {(f.fieldname or '').lower()}"
        if any(bad in haystack for bad in exclude):
            continue
        if any(kw in haystack for kw in keywords):
            return f.fieldname
    return None
