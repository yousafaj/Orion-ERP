"""Reconcile completed, attendance-supported months after legacy checkpoints."""


def execute():
    from orion_erp.orion_erp.scripts.annual_leave_accrual import execute_monthly_accrual

    execute_monthly_accrual()
