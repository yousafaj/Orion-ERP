import frappe
import re
from frappe.utils import nowdate


def _normalize(name):
    return re.sub(r'[^a-z0-9_]', '', name.lower().replace(' ', '_').replace('/', '_').replace('-', '_'))


def _get_balance_for(leave_type, employee):
    if not employee:
        return 0
    rows = frappe.get_all(
        "Leave Allocation",
        filters={
            "docstatus": 1,
            "employee": employee,
            "leave_type": leave_type,
            "to_date": [">=", nowdate()],
        },
        fields=["total_leaves_allocated", "custom_carry_forward_days", "custom_lapsed_leave_days", "total_leaves_encashed"]
    )
    return sum(
        (r.total_leaves_allocated or 0)
        + (r.custom_carry_forward_days or 0)
        - (r.custom_lapsed_leave_days or 0)
        - (r.total_leaves_encashed or 0)
        for r in rows
    )


def _make_balance_fn(leave_type):
    @frappe.whitelist()
    def _fn():
        employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        balance = _get_balance_for(leave_type, employee)
        return {
            "value": balance,
            "fieldtype": "Float",
            "route": ["List", "Leave Allocation"],
            "route_options": {"employee": employee, "leave_type": leave_type, "docstatus": 1},
        }
    _fn.__name__ = _normalize(leave_type) + "_balance"
    _fn.__qualname__ = _fn.__name__
    return _fn


_leave_type_cache = None


def _get_method_map():
    global _leave_type_cache
    if _leave_type_cache is not None:
        return _leave_type_cache
    _leave_type_cache = {}
    for lt in frappe.get_all("Leave Type", pluck="name"):
        _leave_type_cache[_normalize(lt) + "_balance"] = lt
    return _leave_type_cache


def __getattr__(name):
    if name.startswith("_"):
        raise AttributeError(name)
    mapping = _get_method_map()
    if name in mapping:
        return _make_balance_fn(mapping[name])
    raise AttributeError(f"module 'leave_balance_cards' has no attribute '{name}'")
