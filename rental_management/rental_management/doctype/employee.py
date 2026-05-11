import frappe
from frappe.utils import today, date_diff, add_years, add_days,flt,getdate,add_months

def validate_allowance_amounts(doc, method=None):

    if doc.custom_site_allowances:

        if not doc.custom_site_allowances_amount or doc.custom_site_allowances_amount <= 0:

            frappe.throw(
                "Site Allowance Amount must be greater than 0 when Site Allowance is checked."
            )

    if doc.custom_offshore_allowances:

        if (
            not doc.custom_offshore_allowances_amount
            or doc.custom_offshore_allowances_amount <= 0
        ):

            frappe.throw(
                "Offshore Allowance Amount must be greater than 0 when Offshore Allowance is checked."
            )

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def user_by_employee(doctype, txt, searchfield, start, page_len, filters):

    users = frappe.db.sql("""
        SELECT
            e.user_id as value,
            CONCAT(e.name, ' - ', e.employee_name) as description
        FROM
            `tabEmployee` e
        WHERE
            e.user_id IS NOT NULL
            AND e.user_id != ''
            AND e.status = 'Active'
            AND (e.name LIKE %(txt)s OR e.employee_name LIKE %(txt)s)
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })

    return users

def create_ticket_allowance():

    settings = frappe.get_single("Orion Settings")

    if not settings.ticket_entitlement_detail:
        return

    employees = frappe.get_all(
        "Employee",
        fields=["name", "designation", "date_of_joining"]
    )

    today_date = getdate(today())

    for emp in employees:

        if not emp.date_of_joining or not emp.designation:
            continue

        for rule in settings.ticket_entitlement_detail:

            if not rule.designations:
                continue

            designation_list = [d.strip() for d in rule.designations.split(",")]

            if emp.designation not in designation_list:
                continue

            # Convert eligibility years to months for cycle calculation
            cycle_months = int(flt(rule.eligible_after_years_from_doj) * 12)

            # First eligibility date
            first_cycle_start = add_months(emp.date_of_joining, cycle_months)

            current_start = first_cycle_start

            # Generate ticket cycles until today
            while current_start <= today_date:

                from_date = current_start
                to_date = add_days(add_months(current_start, cycle_months), -1)

                # Avoid duplicate records
                exists = frappe.db.exists(
                    "Ticket Allowance Detail",
                    {
                        "parent": emp.name,
                        "parenttype": "Employee",
                        "from_date": from_date
                    }
                )

                if not exists:
                    # Create ticket allowance child record
                    frappe.get_doc({
                        "doctype": "Ticket Allowance Detail",
                        "parent": emp.name,
                        "parentfield": "custom_ticket_allowance_detail",
                        "parenttype": "Employee",
                        "from_date": from_date,
                        "to_date": to_date,
                        "amount": rule.amount,
                        "paid": 0
                    }).insert(ignore_permissions=True)

                # Move to next cycle
                current_start = add_months(current_start, cycle_months)


@frappe.whitelist()
def get_manual_paid_lock_date():
    # Return lock date from Orion Settings
    return frappe.db.get_single_value(
        "Orion Settings",
        "manual_paid_check_read_only_date"
    )


def create_salary_structure_assignment(doc, method):

    if not doc.custom_salary_structure or not doc.date_of_joining:
        return

    # Check if SSA already exists for this employee & DOJ
    exists = frappe.db.exists("Salary Structure Assignment", {
        "employee": doc.name,
        "from_date": getdate(doc.date_of_joining),
        "docstatus": ["!=", 2]  
    })

    if exists:
        return  

    # Create SSA
    ssa = frappe.new_doc("Salary Structure Assignment")
    ssa.employee = doc.name
    ssa.salary_structure = doc.custom_salary_structure
    ssa.from_date = doc.date_of_joining
    ssa.base = doc.custom_total_salary_as_per_offer_letter or 0

    ssa.company = doc.company

    ssa.insert(ignore_permissions=True)
    ssa.submit()

@frappe.whitelist()
def check_salary_structure_assignment(employee, doj):

    return frappe.db.exists(
        "Salary Structure Assignment",
        {
            "employee": employee,
            "from_date": doj,
            "docstatus": ["!=", 2]
        }
    )