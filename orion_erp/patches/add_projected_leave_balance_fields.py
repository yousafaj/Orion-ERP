"""Add read-only forecast fields; do not change balances or approval rights."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({"Leave Application": [
        dict(fieldname="custom_current_leave_balance", label="Current Credited Leave Balance",
             fieldtype="Float", read_only=1, insert_after="leave_balance",
             description="Ledger balance as of today, before unsubmitted requests."),
        dict(fieldname="custom_projected_leave_accrual", label="Expected Accrual Before Leave Starts",
             fieldtype="Float", read_only=1, insert_after="custom_current_leave_balance",
             description="Forecast only; actual credits still require the normal accrual process."),
        dict(fieldname="custom_pending_leave_reserved", label="Other Pending Leave Reserved",
             fieldtype="Float", read_only=1, insert_after="custom_projected_leave_accrual"),
    ]}, update=True)
