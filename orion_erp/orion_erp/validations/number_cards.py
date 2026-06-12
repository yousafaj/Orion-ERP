import frappe
from frappe.utils import nowdate, add_days
from frappe import _

# Reusable
def get_expiring_count(start_date, end_date, employee_only=False, customer_only=False):
    filters = {
        "date_of_expiry": ["between", [start_date, end_date]],
        "mark_as_not_renew": 0
    }
    if employee_only:
        filters["employee"] = ["is", "set"]
    elif customer_only:
        filters["customer"] = ["is", "set"]
    else:
        filters["employee"] = ["is", "not set"]
        filters["customer"] = ["is", "not set"]
    return frappe.db.count("Existing Certificates", filters=filters)

def get_expired_count(employee_only=False, customer_only=False):
    filters = {
        "date_of_expiry": ["<", nowdate()],
        "mark_as_not_renew": 0
    }
    if employee_only:
        filters["employee"] = ["is", "set"]
    elif customer_only:
        filters["customer"] = ["is", "set"]
    else:
        filters["employee"] = ["is", "not set"]
        filters["customer"] = ["is", "not set"]
    return frappe.db.count("Existing Certificates", filters=filters)

def get_total_employee_certs():
    return frappe.db.count("Existing Certificates", filters={"employee": ["is", "set"]})

def get_total_customer_certs():
    return frappe.db.count("Existing Certificates", filters={"customer": ["is", "set"]})

@frappe.whitelist()
def expired():
    count = get_expired_count()
    return create_route_options(count, "<", nowdate())

@frappe.whitelist()
def expire_in_10_days():
    today = nowdate()
    ten_days = add_days(today, 10)
    count = get_expiring_count(today, ten_days)
    return create_route_options(count, "between", [today, ten_days])

@frappe.whitelist()
def expire_in_30_days():
    today = nowdate()
    thirty_days = add_days(today, 30)
    count = get_expiring_count(today, thirty_days)
    return create_route_options(count, "between", [today, thirty_days])

@frappe.whitelist()
def expire_in_60_days():
    today = nowdate()
    sixty_days = add_days(today, 60)
    count = get_expiring_count(today, sixty_days)
    return create_route_options(count, "between", [today, sixty_days])

@frappe.whitelist()
def total_employee_certifications():
    count = get_total_employee_certs()
    return create_route_options(count, employee_set=True)

@frappe.whitelist()
def employee_expired():
    count = get_expired_count(employee_only=True)
    return create_route_options(count, "<", nowdate(), employee_set=True)

@frappe.whitelist()
def employee_expire_in_10_days():
    today = nowdate()
    ten_days = add_days(today, 10)
    count = get_expiring_count(today, ten_days, employee_only=True)
    return create_route_options(count, "between", [today, ten_days], employee_set=True)

@frappe.whitelist()
def employee_expire_in_30_days():
    today = nowdate()
    thirty_days = add_days(today, 30)
    count = get_expiring_count(today, thirty_days, employee_only=True)
    return create_route_options(count, "between", [today, thirty_days], employee_set=True)

@frappe.whitelist()
def employee_expire_in_60_days():
    today = nowdate()
    sixty_days = add_days(today, 60)
    count = get_expiring_count(today, sixty_days, employee_only=True)
    return create_route_options(count, "between", [today, sixty_days], employee_set=True)

@frappe.whitelist()
def total_customer_certifications():
    count = get_total_customer_certs()
    return create_route_options(count, customer_set=True)

@frappe.whitelist()
def customer_expired():
    count = get_expired_count(customer_only=True)
    return create_route_options(count, "<", nowdate(), customer_set=True)

@frappe.whitelist()
def customer_expire_in_10_days():
    today = nowdate()
    ten_days = add_days(today, 10)
    count = get_expiring_count(today, ten_days, customer_only=True)
    return create_route_options(count, "between", [today, ten_days], customer_set=True)

@frappe.whitelist()
def customer_expire_in_30_days():
    today = nowdate()
    thirty_days = add_days(today, 30)
    count = get_expiring_count(today, thirty_days, customer_only=True)
    return create_route_options(count, "between", [today, thirty_days], customer_set=True)

@frappe.whitelist()
def customer_expire_in_60_days():
    today = nowdate()
    sixty_days = add_days(today, 60)
    count = get_expiring_count(today, sixty_days, customer_only=True)
    return create_route_options(count, "between", [today, sixty_days], customer_set=True)

@frappe.whitelist()
def marked_not_renew():
    return get_marked_not_renew(employee_set=False)

@frappe.whitelist()
def marked_not_renew_employees():
    return get_marked_not_renew(employee_set=True)

def get_marked_not_renew(employee_set=True):
    filters = {"mark_as_not_renew": 1}
    filters["employee"] = ["is", "set"] if employee_set else ["is", "not set"]
    count = frappe.db.count("Existing Certificates", filters=filters)
    return {
        "value": count,
        "fieldtype": "Int",
        "label": _(f"Marked Not for Renewal {'(Employees)' if employee_set else ''}"),
        "route": ["List", "Existing Certificates"],
        "route_options": filters
    }

@frappe.whitelist()
def un_invoiced_months():
    """Submitted Monthly Billing sheets not yet marked invoiced — so a month is
    never missed. Priority dashboard card."""
    count = frappe.db.count("Monthly Billing", {"docstatus": 1, "invoiced": 0})
    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Monthly Billing"],
        "route_options": {"invoiced": 0, "docstatus": 1},
    }


@frappe.whitelist()
def loa_quota_remaining():
    """Total remaining vehicle + driver CICPA quota across active LOAs."""
    rows = frappe.get_all(
        "LOA",
        filters={"docstatus": 1, "loa_status": "Active"},
        fields=["remaining_vehicle_quota", "remaining_driver_quota"],
    )
    total = sum((r.remaining_vehicle_quota or 0) + (r.remaining_driver_quota or 0) for r in rows)
    return {
        "value": total,
        "fieldtype": "Int",
        "route": ["List", "LOA"],
        "route_options": {"loa_status": "Active"},
    }


@frappe.whitelist()
def vehicles_rent_ending_30d():
    """Rented vehicles whose rent ends within 30 days — renew/return before lapse."""
    today = nowdate()
    soon = add_days(today, 30)
    count = frappe.db.count(
        "Vehicle",
        {"custom_status": "Active", "custom_rent_end_date": ["between", [today, soon]]},
    )
    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Vehicle"],
        "route_options": {"custom_rent_end_date": ["between", [today, soon]]},
    }


def create_route_options(count, date_filter_type=None, date_filter_value=None, employee_set=False, customer_set=False):
    route_options = {"mark_as_not_renew": 0}
    if date_filter_type:
        route_options["date_of_expiry"] = [date_filter_type, date_filter_value]
    if employee_set:
        route_options["employee"] = ["is", "set"]
    elif customer_set:
        route_options["customer"] = ["is", "set"]
    else:
        route_options["employee"] = ["is", "not set"]
        route_options["customer"] = ["is", "not set"]

    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Existing Certificates"],
        "route_options": route_options
    }
