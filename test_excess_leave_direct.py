"""Direct test script for excess leave functionality.
Run: env/bin/python3 apps/orion_erp/test_excess_leave_direct.py --site site1.local
"""
import sys
import os

os.environ["GIT_PYTHON_REFRESH"] = "quiet"

site = sys.argv[sys.argv.index("--site") + 1] if "--site" in sys.argv else "site1.local"

# Change to bench directory so frappe can find sites/
bench_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(bench_dir)

import frappe

frappe.init(site=site)
frappe.connect()

leave_types = frappe.db.get_list("Leave Type", pluck="name")
print(f"Available Leave Types: {leave_types}")

if "ANNUAL LEAVE" in leave_types:
    lt = frappe.get_doc("Leave Type", "ANNUAL LEAVE")
    print(f"ANNUAL LEAVE max_carry: {lt.maximum_carry_forwarded_leaves}")

    active_emps = frappe.get_all("Employee", filters={"status": "Active"}, limit=5, pluck="name")
    print(f"\nActive employees (first 5): {active_emps}")

    for emp in active_emps:
        from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
        balance = get_leave_balance_on(emp, "ANNUAL LEAVE", frappe.utils.today())
        print(f"  {emp}: balance={balance}")

    cf_allocs = frappe.get_all(
        "Leave Allocation",
        filters={
            "leave_type": "ANNUAL LEAVE",
            "description": ["like", "%Carry Forward%"],
            "docstatus": 1
        },
        fields=["name", "employee", "custom_excess_leave_days", "custom_excess_leave_status",
                "custom_carry_forward_days", "custom_decision_date", "custom_decided_by"],
        limit=10
    )
    print(f"\nCarry Forward allocations with excess tracking ({len(cf_allocs)} found):")
    for a in cf_allocs:
        print(f"  {a.name} | emp={a.employee} | excess={a.custom_excess_leave_days} | status={a.custom_excess_leave_status}")

    from orion_erp.orion_erp.report.excess_leave_report.excess_leave_report import get_data
    data = get_data({})
    print(f"\nExcess Leave Report rows: {len(data)}")
    for row in data:
        print(f"  {row.employee}: balance={row.current_balance}, excess={row.excess_days}, action={row.action_status}")

else:
    print("ANNUAL LEAVE not found - checking other leave types...")
    for lt_name in leave_types:
        lt = frappe.get_doc("Leave Type", lt_name)
        print(f"  {lt_name}: max_carry={lt.maximum_carry_forwarded_leaves}")

frappe.db.close()
