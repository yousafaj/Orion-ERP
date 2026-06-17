import frappe
from frappe.utils import flt


def before_submit(doc, method):
    excess = flt(doc.custom_excess_leave_days)
    if excess <= 0:
        return

    status = doc.custom_excess_leave_status or "Pending"

    if status == "Pending":
        frappe.throw(
            "Please take action on the excess leave days before submitting."
        )

    if status == "Forfeit":
        doc.custom_lapsed_leave_days = excess
        doc.custom_carry_forward_days = 0

    if status == "Extend":
        cf_days = flt(doc.custom_carry_forward_days)
        if cf_days <= 0:
            frappe.throw("Carry Forward Days must be greater than 0")
        if cf_days > excess:
            frappe.throw(
                f"Carry Forward Days ({cf_days}) cannot exceed "
                f"Excess Leave Days ({excess})"
            )
        lapsed = flt(doc.custom_lapsed_leave_days)
        if flt(lapsed + cf_days) != excess:
            frappe.throw(
                f"Carry Forward Days ({cf_days}) + Lapsed Days ({lapsed}) "
                f"must equal Excess Leave Days ({excess})"
            )
        doc.custom_lapsed_leave_days = lapsed
