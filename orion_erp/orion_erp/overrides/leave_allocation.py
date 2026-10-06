"""Keep office annual-leave adjustments consistent across company transfers."""

import frappe
from frappe.utils import flt
from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation
from orion_erp.orion_erp.overrides.leave_application import uses_projected_balance


class OrionLeaveAllocation(LeaveAllocation):
    def get_existing_leave_count(self):
        if (frappe.db.get_value("Employee", self.employee, "custom_employee_category") != "Office"
                or not uses_projected_balance(self.leave_type)):
            return super().get_existing_leave_count()

        # Imported allocations can retain the previous company while subsequent
        # credits fetch the employee's current company. All credits belonging to
        # this allocation must count when HRMS posts the difference after an edit.
        # Preserve native carry-forward, cancellation and expiry semantics.
        entries = frappe.get_all("Leave Ledger Entry", filters={
            "transaction_type": "Leave Allocation",
            "transaction_name": self.name,
            "employee": self.employee,
            "leave_type": self.leave_type,
            "is_carry_forward": 0,
            "docstatus": 1,
        }, fields=["SUM(leaves) as total_leaves"])
        return flt(entries[0].total_leaves) if entries else 0.0
