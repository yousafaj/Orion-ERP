import frappe
from frappe import _
from frappe.utils import get_first_day, get_last_day, getdate, formatdate


def validate_installment_amount(self):
    def check_rows(rows, table_name):
        for row in rows:
            if row.installment_amount is None:
                continue
            if row.installment_amount <= 0:
                frappe.throw(
                    f"{table_name} Row #{row.idx}: "
                    "Installment Amount must be greater than 0"
                )
            if row.remaining_amount and row.installment_amount > row.remaining_amount:
                frappe.throw(
                    f"{table_name} Row #{row.idx}: "
                    f"Installment Amount ({row.installment_amount}) "
                    f"cannot be greater than Remaining Amount ({row.remaining_amount})"
                )

    check_rows(self.employee_deduction_detail or [], "Employee Deduction Detail")
    check_rows(self.outstanding_employee_deduction_detail or [], "Outstanding Deduction Detail")


@frappe.whitelist()
def get_outstanding_penalties(employee):
    if not employee:
        return []

    parent = frappe.get_all(
        "Employee Deduction",
        filters={"employee": employee, "docstatus": 1},
        fields=["name"],
        order_by="creation desc",
        limit=1
    )
    if not parent:
        return []

    doc = frappe.get_doc("Employee Deduction", parent[0].name)
    return _collect_outstanding_rows(doc, parent[0].name)


def _collect_outstanding_rows(doc, parent_name):
    result = []

    for row in doc.employee_deduction_detail or []:
        if (row.remaining_amount or 0) <= 0:
            continue
        installment_amount = min(row.remaining_amount, row.installment_amount)
        result.append(_build_penalty_row(row, parent_name, "current", parent_ref=parent_name))

    for row in doc.outstanding_employee_deduction_detail or []:
        if (row.remaining_amount or 0) <= 0:
            continue
        result.append(_build_penalty_row(row, None, "outstanding", parent_ref=row.parent_ref))

    return result


def _build_penalty_row(row, parent_name, source, parent_ref=None):
    return {
        "type_of_penalty": row.type_of_penalty,
        "deduction_date": row.deduction_date,
        "payroll_start_date": row.payroll_start_date,
        "payrol_end_date": row.payrol_end_date,
        "deduction_amount": row.deduction_amount,
        "installment": row.installment,
        "installment_amount": min(row.remaining_amount, row.installment_amount),
        "paid_amount": row.paid_amount,
        "remaining_amount": row.remaining_amount,
        "status": row.status,
        "reference": row.reference,
        "remarks": row.remarks,
        "attachment_1": row.attachment_1,
        "attachment_2": row.attachment_2,
        "parent_ref": parent_ref,
        "child_ref": row.name if source == "current" else row.child_ref,
        "source": source,
        "additional_deduction_ref": row.additional_deduction_ref
    }


@frappe.whitelist()
def run_deduction_manual(employee_type):
    settings = frappe.get_single("Orion Settings")

    if employee_type == "Office":
        _process_office_deductions(settings)
    elif employee_type == "Non-Office":
        _process_non_office_deductions(settings)


def _process_office_deductions(settings):
    if not settings.payroll_month_date_oe:
        frappe.throw("Please set Payroll Month Date for Office.")

    end_date = get_last_day(settings.payroll_month_date_oe)
    process_deductions("Office", settings.payroll_month_date_oe)
    settings.db_set("last_month_for_which_payment_processed_oe", end_date, update_modified=False)
    frappe.msgprint("Office deductions processed successfully.")


def _process_non_office_deductions(settings):
    if not settings.payroll_month_date_noe:
        frappe.throw("Please set Payroll Month Date for Non-Office.")

    end_date = get_last_day(settings.payroll_month_date_noe)
    process_deductions("Non-Office", settings.payroll_month_date_noe)
    settings.db_set("last_month_for_which_payment_processed_noe", end_date, update_modified=False)
    frappe.msgprint("Non-Office deductions processed successfully.")


@frappe.whitelist()
def run_deduction_cron():
    settings = frappe.get_single("Orion Settings")
    today = getdate()

    cron_oe = getdate(settings.cron_schedule_date_oe) if settings.cron_schedule_date_oe else None
    cron_noe = getdate(settings.cron_schedule_date_noe) if settings.cron_schedule_date_noe else None

    if cron_oe and today == cron_oe:
        end_date = get_last_day(settings.payroll_month_date_oe)
        process_deductions("Office", settings.payroll_month_date_oe)
        settings.db_set("last_month_for_which_payment_processed_oe", end_date, update_modified=False)

    if cron_noe and today == cron_noe:
        end_date = get_last_day(settings.payroll_month_date_noe)
        process_deductions("Non-Office", settings.payroll_month_date_noe)
        settings.db_set("last_month_for_which_payment_processed_noe", end_date, update_modified=False)


def process_deductions(category, payroll_date):
    if not payroll_date:
        return

    payroll_date = getdate(payroll_date)
    start_date = get_first_day(payroll_date)
    end_date = get_last_day(payroll_date)

    employees = frappe.get_all(
        "Employee",
        filters={"custom_employee_category": category},
        pluck="name"
    )

    for emp in employees:
        _process_employee_deduction(emp, start_date, end_date, category)


def _process_employee_deduction(emp, start_date, end_date, category):
    try:
        if frappe.db.exists("Additional Salary", {
            "employee": emp, "payroll_date": end_date,
            "salary_component": "Total Deduction", "docstatus": 1
        }):
            return

        doc_name = frappe.db.get_value(
            "Employee Deduction", {"employee": emp, "docstatus": 1},
            "name", order_by="creation desc"
        )
        if not doc_name:
            return

        doc = frappe.get_doc("Employee Deduction", doc_name)
        picked_rows = _pick_applicable_rows(doc, start_date, end_date)

        if not picked_rows:
            return

        create_deduction_additional_salary(emp, end_date, picked_rows)
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            title=f"Deduction Cron Failed for Employee {emp}",
            message=frappe.get_traceback()
        )


def _pick_applicable_rows(doc, start_date, end_date):
    picked_rows = []

    for row in doc.employee_deduction_detail or []:
        if _is_row_applicable(row, start_date, end_date):
            picked_rows.append({"row": row, "doctype": "Employee Deduction Detail"})

    for row in doc.outstanding_employee_deduction_detail or []:
        if _is_row_applicable(row, start_date, end_date):
            picked_rows.append({"row": row, "doctype": "Outstanding Employee Deduction Detail"})

    return picked_rows


def _is_row_applicable(row, start_date, end_date):
    if (row.remaining_amount or 0) <= 0:
        return False
    if not row.payroll_start_date:
        return False

    row_start = row.payroll_start_date
    row_end = row.payrol_end_date or end_date
    return row_start <= end_date and row_end >= start_date


def create_deduction_additional_salary(employee, payroll_date, picked_rows):
    emp = frappe.get_doc("Employee", employee)

    doc = frappe.new_doc("Additional Salary")
    doc.employee = employee
    doc.company = emp.company
    doc.salary_component = "Total Deduction"
    doc.payroll_date = payroll_date
    doc.custom_auto_generated = 1

    total = 0
    for item in picked_rows:
        row = item["row"]
        installment = min(row.installment_amount or 0, row.remaining_amount or 0)
        if installment <= 0:
            continue

        child = doc.append("custom_penalties_detail", {})
        child.employee_deduction_reference = row.name
        child.penalty_name = row.type_of_penalty
        child.remaining_amount = row.remaining_amount
        child.installation_amount = installment
        child.deduction_date = row.deduction_date
        child.remarks = row.remarks
        total += installment

    if total <= 0:
        return

    doc.amount = total
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc


def sync_to_outstanding(self, row):
    if not (row.has_value_changed("paid") or row.has_value_changed("partial_paid")):
        return

    match_row = frappe.db.sql("""
        SELECT name, parent_ref, child_ref, parent
        FROM `tabOutstanding Employee Deduction Detail`
        WHERE parent_ref = %s
        ORDER BY creation DESC
        LIMIT 1
    """, (self.name,), as_dict=True)

    if not match_row:
        return

    match_row = match_row[0]

    if match_row.child_ref:
        frappe.db.sql("""
            UPDATE `tabOutstanding Employee Deduction Detail`
            SET paid_amount = %s, remaining_amount = %s, status = %s
            WHERE name = %s
        """, (row.paid_amount, row.remaining_amount, row.status, match_row.name))

    if match_row.parent_ref:
        parent_doc = frappe.get_doc("Employee Deduction", match_row.parent)
        parent_doc.update_parent_totals()
        frappe.db.set_value(
            "Employee Deduction", parent_doc.name,
            {
                "paid_amount": parent_doc.paid_amount,
                "remaining_balance": parent_doc.remaining_balance,
                "status": parent_doc.status
            },
            update_modified=False
        )


def validate_payroll_dates(doc, method=None):
    processed_periods = frappe.get_all(
        "Process Employee Deductions",
        filters={"docstatus": 1, "employee_category": doc.employee_category},
        fields=["payroll_start_date", "payroll_date_date", "name"],
        order_by="payroll_start_date asc"
    )

    for row in doc.employee_deduction_detail or []:
        _validate_single_row_payroll_dates(row, processed_periods)


def _validate_single_row_payroll_dates(row, processed_periods):
    payroll_start_date = getdate(row.payroll_start_date) if row.payroll_start_date else None
    payroll_end_date = getdate(row.payrol_end_date) if row.payrol_end_date else None

    if payroll_start_date and payroll_end_date and payroll_end_date < payroll_start_date:
        frappe.throw(
            f"<b>Invalid Payroll Dates in Row #{row.idx}</b><br><br>"
            f"Payroll End Date: <b>{formatdate(payroll_end_date)}</b> "
            f"cannot be earlier than Payroll Start Date: <b>{formatdate(payroll_start_date)}</b>."
        )

    if payroll_start_date:
        for p in processed_periods:
            proc_start = getdate(p.payroll_start_date)
            proc_end = getdate(p.payroll_date_date)
            if proc_start <= payroll_start_date <= proc_end:
                frappe.throw(
                    f"<b>Payroll Period Already Processed</b><br><br>"
                    f"Row #{row.idx} has Payroll Start Date: <b>{formatdate(payroll_start_date)}</b> "
                    f"which falls within an already processed payroll period: "
                    f"<b>{formatdate(proc_start)} to {formatdate(proc_end)}</b><br><br>"
                    f"Process Employee Deduction: <b>{p.name}</b><br><br>"
                    f"Please select a payroll date after <b>{formatdate(proc_end)}</b>."
                )
