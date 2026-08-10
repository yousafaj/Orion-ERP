import frappe


def auto_expire_loas():
    today = frappe.utils.nowdate()
    candidates = frappe.get_all(
        "LOA",
        filters={"docstatus": 1, "loa_status": "Active", "expiry_date": ["<", today]},
        pluck="name",
    )
    for name in candidates:
        try:
            frappe.db.set_value(
                "LOA", name,
                {"loa_status": "Expired", "active": 0},
                update_modified=True,
            )
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), f"auto_expire_loas failed for {name}")
