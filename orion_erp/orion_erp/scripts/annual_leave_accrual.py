import frappe
from frappe.utils import getdate, add_months, add_days, flt
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

LEAVE_TYPE = "ANNUAL LEAVE"


def execute_monthly_accrual():
    rules = get_rules_from_leave_type()

    if not rules:
        return

    today = getdate()

    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "date_of_joining": ["<=", today]
        },
        fields=["name", "date_of_joining"]
    )

    for emp in employees:
        try:
            doj = getdate(emp.date_of_joining)

            completed_months = get_completed_months(doj, today)

            if completed_months < 1:
                continue

            anniversary_date = add_months(doj, completed_months)

            if anniversary_date != today:
                continue

            process_employee(
                emp.name,
                doj,
                completed_months,
                rules
            )

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Monthly Accrual Failed - {emp.name}"
            )


def process_employee(employee, doj, month_num, rules):
    rate = get_rate_for_month(month_num, rules)

    if not rate:
        return

    year_start = get_year_start(doj, month_num)
    year_end = get_year_end(doj, month_num)

    service_start = add_months(doj, month_num - 1)
    service_end = add_days(add_months(doj, month_num), -1)

    description = (
        f"Month {month_num} "
        f"({service_start.strftime('%d %B %Y')} - "
        f"{service_end.strftime('%d %B %Y')})"
    )

    if frappe.db.exists(
        "Leave Allocation",
        {
            "employee": employee,
            "leave_type": LEAVE_TYPE,
            "description": description,
            "docstatus": 1
        }
    ):
        return

    if not has_attendance_in_period(
        employee,
        service_start,
        service_end
    ):
        return

    allocation = frappe.new_doc("Leave Allocation")
    allocation.employee = employee
    allocation.leave_type = LEAVE_TYPE
    allocation.from_date = year_start
    allocation.to_date = year_end
    allocation.new_leaves_allocated = flt(rate, 2)
    allocation.description = description

    allocation.flags.ignore_permissions = True
    allocation.insert(ignore_permissions=True)
    allocation.submit()


def get_rules_from_leave_type():
    leave_type = frappe.get_cached_doc("Leave Type", LEAVE_TYPE)

    rules = sorted(
        leave_type.custom_annual_leave_accrual_rules or [],
        key=lambda x: x.from_months
    )

    return [
        {
            "from_months": r.from_months,
            "to_months": r.to_months,
            "days_per_month": flt(r.days_per_month)
        }
        for r in rules
    ]


def get_rate_for_month(month_num, rules):
    for rule in rules:

        if rule["to_months"] == 0:
            if month_num >= rule["from_months"]:
                return rule["days_per_month"]

        elif rule["from_months"] <= month_num <= rule["to_months"]:
            return rule["days_per_month"]

    return 0


def get_completed_months(from_date, to_date):
    months = (
        (to_date.year - from_date.year) * 12
        + (to_date.month - from_date.month)
    )

    if to_date.day < from_date.day:
        months -= 1

    return max(months, 0)


def get_year_start(doj, month_num):
    anniversary_index = ((month_num - 1) // 12) * 12
    return add_months(doj, anniversary_index)


def get_year_end(doj, month_num):
    anniversary_index = ((month_num - 1) // 12) * 12
    return add_days(
        add_months(doj, anniversary_index + 12),
        -1
    )


def has_attendance_in_period(employee, from_date, to_date):
    return frappe.db.exists(
        "Attendance",
        {
            "employee": employee,
            "attendance_date": ["between", [from_date, to_date]],
            "status": ["in", ["Present", "Half Day"]],
            "docstatus": 1
        }
    )


#carry forward logic


def execute_carry_forward():
    today = getdate()

    print("\n" + "=" * 100)
    print("STARTING CARRY FORWARD")
    print("TODAY:", today)
    print("=" * 100)

    leave_type = frappe.get_cached_doc(
        "Leave Type",
        LEAVE_TYPE
    )

    print("Leave Type:", leave_type.name)

    max_carry = flt(
        leave_type.maximum_carry_forwarded_leaves or 0
    )

    print("Maximum Carry Forward:", max_carry)

    if not max_carry:
        print("Maximum Carry Forward is 0. Exiting.")
        return

    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "date_of_joining": ["<=", today]
        },
        fields=["name", "employee_name", "date_of_joining"]
    )

    print("Total Employees Found:", len(employees))

    for emp in employees:

        print("\n" + "-" * 100)
        print("Employee:", emp.name)
        print("DOJ:", emp.date_of_joining)

        doj = getdate(emp.date_of_joining)

        completed_months = get_completed_months(
            doj,
            today
        )

        print("Completed Months:", completed_months)

        if (
            completed_months < 12
            or completed_months % 12 != 0
        ):
            print(
                f"SKIPPED -> Not Year End. "
                f"Months={completed_months}"
            )
            continue

        print("Passed Year-End Check")

        anniversary_date = add_months(
            doj,
            completed_months
        )

        print("Anniversary Date:", anniversary_date)
        print("Today:", today)

        if anniversary_date != today:
            print("SKIPPED -> Anniversary Date Mismatch")
            continue

        print("Passed Anniversary Check")

        leave_year_end = add_days(
            add_months(doj, completed_months),
            -1
        )

        print("Leave Year End:", leave_year_end)

        try:
            balance = flt(
                get_leave_balance_on(
                    emp.name,
                    LEAVE_TYPE,
                    leave_year_end
                )
            )

            print("Balance:", balance)

        except Exception:
            print("ERROR FETCHING BALANCE")
            print(frappe.get_traceback())
            continue

        carry_forward = min(
            balance,
            max_carry
        )

        print("Carry Forward Amount:", carry_forward)

        if carry_forward <= 0:
            print("SKIPPED -> No Carry Forward Balance")
            continue

        description = (
            f"Carry Forward Year "
            f"{completed_months // 12}"
        )

        print("Description:", description)

        existing = frappe.db.exists(
            "Leave Allocation",
            {
                "employee": emp.name,
                "leave_type": LEAVE_TYPE,
                "description": description,
                "docstatus": 1
            }
        )

        print("Existing Carry Forward:", existing)

        if existing:
            print("SKIPPED -> Carry Forward Already Exists")
            continue

        print("READY TO CREATE CARRY FORWARD")

        create_carry_forward(
            emp.name,
            doj,
            completed_months,
            max_carry
        )

        print("Carry Forward Created Successfully")


def create_carry_forward(
    employee,
    doj,
    completed_months,
    max_carry
):
    print("\nCREATE CARRY FORWARD")
    print("Employee:", employee)

    leave_year_end = add_days(
        add_months(doj, completed_months),
        -1
    )

    print("Leave Year End:", leave_year_end)

    balance = flt(
        get_leave_balance_on(
            employee,
            LEAVE_TYPE,
            leave_year_end
        )
    )

    print("Balance:", balance)

    carry_forward = min(
        balance,
        max_carry
    )

    print("Carry Forward:", carry_forward)

    if carry_forward <= 0:
        print("Skipped - No Balance Available")
        return

    description = (
        f"Carry Forward Year "
        f"{completed_months // 12}"
    )

    print("Description:", description)

    if frappe.db.exists(
        "Leave Allocation",
        {
            "employee": employee,
            "leave_type": LEAVE_TYPE,
            "description": description,
            "docstatus": 1
        }
    ):
        print("Skipped - Carry Forward Already Exists")
        return

    print("Creating Leave Allocation")

    allocation = frappe.new_doc(
        "Leave Allocation"
    )

    allocation.employee = employee
    allocation.leave_type = LEAVE_TYPE

    allocation.from_date = add_months(
        doj,
        completed_months
    )

    allocation.to_date = add_days(
        add_months(doj, completed_months + 12),
        -1
    )

    allocation.new_leaves_allocated = carry_forward
    allocation.description = description

    allocation.flags.ignore_permissions = True

    allocation.insert(
        ignore_permissions=True
    )

    allocation.submit()

    print(
        "Carry Forward Allocation Created:",
        allocation.name
    )

def get_completed_months(from_date, to_date):
    months = (
        (to_date.year - from_date.year) * 12
        + (to_date.month - from_date.month)
    )

    if to_date.day < from_date.day:
        months -= 1

    return max(months, 0)