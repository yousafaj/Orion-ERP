import frappe
from frappe import _
from frappe.utils import getdate, flt
import re
from datetime import timedelta


@frappe.whitelist()
def get_leave_pay_data(employee, date_of_settlement, doj=None):
    if not employee or not date_of_settlement:
        return []

    date_of_settlement = getdate(date_of_settlement)

    from hrms.hr.doctype.leave_application.leave_application import (
        get_leave_balance_on,
        get_leave_allocation_records,
    )

    allocation_records = get_leave_allocation_records(employee, date_of_settlement, "ANNUAL LEAVE")
    allocation = allocation_records.get("ANNUAL LEAVE", frappe._dict())

    if not allocation:
        return []

    balance = get_leave_balance_on(employee, "ANNUAL LEAVE", date_of_settlement)
    leave_balance = flt(balance)

    if leave_balance <= 0:
        return []

    offer_salary = flt(frappe.db.get_value("Employee", employee, "custom_total_salary_as_per_offer_letter"))
    amount = (offer_salary / 30) * leave_balance if offer_salary > 0 else 0

    return [{
        "leave_type": "ANNUAL LEAVE",
        "from": doj,
        "to": str(date_of_settlement),
        "tenure": leave_balance,
        "amount": amount
    }]


@frappe.whitelist()
def get_ticket_allowance(employee, settlement_date, settlement_type=None):
    if not employee or not settlement_date:
        return []

    settlement_date = getdate(settlement_date)

    doj = frappe.db.get_value("Employee", employee, "date_of_joining")
    if not doj:
        return []

    doj = getdate(doj)
    one_year_from_doj = doj + timedelta(days=365)

    if settlement_date < one_year_from_doj:
        return []

    if settlement_type == "Final Settlement":
        return _get_ticket_allowance_for_final_settlement(employee, settlement_date)
    else:
        return _get_ticket_allowance_for_vacation(employee, settlement_date)


def _get_ticket_allowance_for_vacation(employee, settlement_date):
    tickets = frappe.get_all(
        "Ticket Allowance Detail",
        filters={
            "parent": employee,
            "parenttype": "Employee",
            "paid": 0,
            "manual_paid": 0,
            "to_date": ["<", settlement_date]
        },
        fields=["from_date", "to_date", "outstanding_amount"],
        order_by="from_date asc"
    )

    return [
        {"from": t.from_date, "to": t.to_date, "amount": t.outstanding_amount}
        for t in tickets
    ]


def _get_ticket_allowance_for_final_settlement(employee, settlement_date):
    completed_tickets = frappe.get_all(
        "Ticket Allowance Detail",
        filters={
            "parent": employee,
            "parenttype": "Employee",
            "paid": 0,
            "manual_paid": 0,
            "to_date": ["<", settlement_date]
        },
        fields=["from_date", "to_date", "outstanding_amount"],
        order_by="from_date asc"
    )

    result = [
        {"from": t.from_date, "to": t.to_date, "amount": t.outstanding_amount}
        for t in completed_tickets
    ]

    current_cycle_list = frappe.get_all(
        "Ticket Allowance Detail",
        filters={
            "parent": employee,
            "parenttype": "Employee",
            "from_date": ["<=", settlement_date],
            "to_date": [">=", settlement_date]
        },
        fields=["name", "from_date", "to_date", "amount", "paid_amount"],
        limit_page_length=1
    )
    current_cycle = current_cycle_list[0] if current_cycle_list else None

    if current_cycle:
        total_days = (current_cycle.to_date - current_cycle.from_date).days + 1
        if total_days > 0:
            days_elapsed = (settlement_date - current_cycle.from_date).days + 1
            days_elapsed = min(days_elapsed, total_days)
            pro_rata = (flt(current_cycle.amount) / total_days) * days_elapsed
            already_paid = flt(current_cycle.paid_amount)
            payable = max(0, pro_rata - already_paid)

            if payable > 0:
                result.append({
                    "from": str(current_cycle.from_date),
                    "to": str(settlement_date),
                    "amount": flt(payable, 2)
                })

    return result


def mark_ticket_paid(doc, method=None):
    if not doc.ticket_allowance:
        return

    for row in doc.ticket_allowance:
        _mark_single_ticket_paid(doc, row)


def _mark_single_ticket_paid(doc, row):
    ticket_detail = frappe.db.get_value(
        "Ticket Allowance Detail",
        {"parent": doc.employee, "from_date": row.get("from")},
        ["name", "amount", "paid_amount", "references_data"],
        as_dict=True
    )
    if not ticket_detail:
        return

    current_paid_amount = flt(ticket_detail.paid_amount)
    row_amount = flt(row.amount)
    total_paid_amount = current_paid_amount + row_amount
    total_amount = flt(ticket_detail.amount)
    outstanding_amount = max(0, total_amount - total_paid_amount)

    reference_table = _build_ticket_reference_html(ticket_detail, doc, row_amount)

    update_data = {
        "paid_amount": total_paid_amount,
        "outstanding_amount": outstanding_amount,
        "references_data": reference_table
    }

    if total_paid_amount >= total_amount:
        update_data["paid"] = 1
        update_data["partial_paid"] = 0
    else:
        update_data["paid"] = 0
        update_data["partial_paid"] = 1

    frappe.db.set_value("Ticket Allowance Detail", ticket_detail.name, update_data)


def _build_ticket_reference_html(ticket_detail, doc, row_amount):
    existing_reference = ticket_detail.references_data or ""
    new_row = _build_ticket_row_html(doc, row_amount)

    if not existing_reference:
        return _wrap_in_table(new_row)

    if doc.name not in existing_reference:
        return existing_reference.replace("</tbody>", f"{new_row}</tbody>")

    return existing_reference


def _build_ticket_row_html(doc, amount):
    return f"""
        <tr>
            <td><a href="/app/leave-settlement/{doc.name}">{doc.name}</a></td>
            <td>{doc.date_of_settlement}</td>
            <td>{amount}</td>
        </tr>
    """


def _wrap_in_table(row_html):
    return f"""
        <div class="table-responsive">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Leave Settlement</th>
                        <th>Date Of Settlement</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>{row_html}</tbody>
            </table>
        </div>
    """


def revert_ticket_paid(doc, method=None):
    if not doc.ticket_allowance:
        return

    for row in doc.ticket_allowance:
        _revert_single_ticket_paid(doc, row)


def _revert_single_ticket_paid(doc, row):
    ticket_detail = frappe.db.get_value(
        "Ticket Allowance Detail",
        {"parent": doc.employee, "from_date": row.get("from")},
        ["name", "amount", "paid_amount", "references_data"],
        as_dict=True
    )
    if not ticket_detail:
        return

    current_paid_amount = flt(ticket_detail.paid_amount)
    row_amount = flt(row.amount)
    total_amount = flt(ticket_detail.amount)

    total_paid_amount = max(0, current_paid_amount - row_amount)
    outstanding_amount = max(0, total_amount - total_paid_amount)

    reference_html = _remove_ticket_reference(ticket_detail, doc, row_amount)

    update_data = {
        "paid_amount": total_paid_amount,
        "outstanding_amount": outstanding_amount,
        "references_data": reference_html
    }

    if total_paid_amount >= total_amount and total_amount > 0:
        update_data["paid"] = 1
        update_data["partial_paid"] = 0
    elif total_paid_amount > 0:
        update_data["paid"] = 0
        update_data["partial_paid"] = 1
    else:
        update_data["paid"] = 0
        update_data["partial_paid"] = 0

    frappe.db.set_value("Ticket Allowance Detail", ticket_detail.name, update_data)


def _remove_ticket_reference(ticket_detail, doc, row_amount):
    existing_reference = ticket_detail.references_data or ""

    pattern = rf"""
        <tr>\s*
            <td>\s*<a[^>]*>\s*{re.escape(doc.name)}\s*</a>\s*</td>\s*
            <td>\s*{re.escape(str(doc.date_of_settlement))}\s*</td>\s*
            <td>\s*{re.escape(str(row_amount))}\s*</td>\s*
        </tr>
    """

    return re.sub(pattern, "", existing_reference, flags=re.S | re.X)


def validate_ticket_allowance(doc):
    if not doc.ticket_allowance:
        return

    for row in doc.ticket_allowance:
        outstanding_amount = flt(
            frappe.db.get_value(
                "Ticket Allowance Detail",
                {"parent": doc.employee, "from_date": row.get("from")},
                "outstanding_amount"
            )
        )
        if flt(row.amount) > outstanding_amount:
            frappe.throw(
                f"Row #{row.idx}: Ticket Allowance Amount "
                f"cannot be greater than Outstanding Amount ({outstanding_amount})"
            )


def create_leave_settlement_deduction(self):
    if not self.leave_settlement_deductions:
        return

    rows = [
        d for d in self.leave_settlement_deductions
        if not d.skip_penalty_amount and flt(d.amount_to_be_deducted_this_month) > 0
    ]
    if not rows:
        return

    total_amount = sum(flt(d.amount_to_be_deducted_this_month) for d in rows)
    additional_salary = _build_deduction_additional_salary(self, total_amount, rows)
    additional_salary.insert(ignore_permissions=True)
    additional_salary.submit()

    for d in rows:
        d.db_set("additional_salary_ref", additional_salary.name, update_modified=False)


def _build_deduction_additional_salary(self, total_amount, rows):
    additional_salary = frappe.new_doc("Additional Salary")
    additional_salary.employee = self.employee
    additional_salary.employee_name = self.employee_name
    additional_salary.company = self.company
    additional_salary.payroll_date = self.date_of_settlement
    additional_salary.salary_component = "Total Deduction"
    additional_salary.currency = frappe.get_cached_value("Company", self.company, "default_currency")
    additional_salary.amount = total_amount
    additional_salary.overwrite_salary_structure_amount = 1
    additional_salary.custom_auto_generated = 1
    additional_salary.custom_reference_ = self.name

    for d in rows:
        additional_salary.append("custom_penalties_detail", {
            "penalty_name": d.type_of_penalty,
            "installation_amount": d.amount_to_be_deducted_this_month,
            "employee_deduction_reference": d.employee_deduction_reference,
            "date_of_deduction_occurred": d.date_of_deduction_occurred,
            "remaining_amount": d.outstanding_amount
        })

    return additional_salary


def create_ticket_allowance_additional_salary(self):
    if not self.ticket_allowance:
        return

    for row in self.ticket_allowance:
        if flt(row.amount) <= 0:
            continue
        _create_single_ticket_allowance_salary(self, row)


def _create_single_ticket_allowance_salary(self, row):
    additional_salary = frappe.new_doc("Additional Salary")
    additional_salary.employee = self.employee
    additional_salary.employee_name = self.employee_name
    additional_salary.company = self.company
    additional_salary.payroll_date = self.date_of_settlement
    additional_salary.salary_component = "Ticket Allowance"
    additional_salary.currency = frappe.get_cached_value("Company", self.company, "default_currency")
    additional_salary.amount = flt(row.amount)
    additional_salary.overwrite_salary_structure_amount = 1
    additional_salary.custom_auto_generated = 1
    additional_salary.custom_reference_ = self.name
    additional_salary.insert(ignore_permissions=True)
    additional_salary.submit()


def cancel_linked_ticket_allowance_additional_salary(self):
    additional_salaries = frappe.get_all(
        "Additional Salary",
        filters={
            "docstatus": 1,
            "custom_reference_": self.name,
            "salary_component": "Ticket Allowance"
        },
        fields=["name"]
    )
    if not additional_salaries:
        return

    frappe.flags.ignore_ticket_allowance_validation = True
    try:
        for d in additional_salaries:
            doc = frappe.get_doc("Additional Salary", d.name)
            doc.cancel()
    finally:
        frappe.flags.ignore_ticket_allowance_validation = False


def create_leave_encashment_for_settlement(self):
    if self.type_of_settlement != "Final Settlement" or not self.leave_pay:
        return

    leave_period = get_leave_period(self.company, self.date_of_settlement)
    if not leave_period:
        return

    for row in self.leave_pay:
        if flt(row.tenure) <= 0 or flt(row.amount) <= 0:
            continue
        _create_single_leave_encashment(self, row, leave_period)


def _create_single_leave_encashment(self, row, leave_period):
    leave_encashment = frappe.new_doc("Leave Encashment")
    leave_encashment.employee = self.employee
    leave_encashment.employee_name = self.employee_name
    leave_encashment.company = self.company
    leave_encashment.leave_period = leave_period
    leave_encashment.leave_type = row.leave_type
    leave_encashment.encashment_date = self.date_of_settlement
    leave_encashment.encashment_days = flt(row.tenure)
    leave_encashment.encashment_amount = flt(row.amount)
    leave_encashment.currency = frappe.get_cached_value("Company", self.company, "default_currency")
    leave_encashment.custom_leave_settlement_ref = self.name
    leave_encashment.pay_via_payment_entry = 0
    leave_encashment.flags.ignore_permissions = True

    if not frappe.flags.get("_leave_encashment_overrides"):
        frappe.flags._leave_encashment_overrides = {}

    frappe.flags._leave_encashment_overrides[self.employee] = {
        "amount": flt(row.amount),
        "days": flt(row.tenure),
    }

    leave_encashment.insert(ignore_permissions=True)
    leave_encashment.submit()


def cancel_linked_leave_encashments(self):
    leave_encashments = frappe.get_all(
        "Leave Encashment",
        filters={"docstatus": 1, "custom_leave_settlement_ref": self.name},
        fields=["name"]
    )

    for d in leave_encashments:
        _cancel_single_leave_encashment(d.name)


def _cancel_single_leave_encashment(encashment_name):
    additional_salary_name = frappe.db.get_value(
        "Additional Salary",
        {"ref_doctype": "Leave Encashment", "ref_docname": encashment_name, "docstatus": 1},
        "name"
    )

    if additional_salary_name:
        add_doc = frappe.get_doc("Additional Salary", additional_salary_name)
        if add_doc.docstatus == 1:
            add_doc.cancel()

    doc = frappe.get_doc("Leave Encashment", encashment_name)
    doc.additional_salary = ""
    doc.flags.ignore_links = True
    doc.cancel()


def cancel_linked_additional_deductions(self):
    additional_salary_list = list(set([
        row.additional_salary_ref
        for row in self.leave_settlement_deductions
        if row.additional_salary_ref
    ]))
    if not additional_salary_list:
        return

    additional_deductions = frappe.get_all(
        "Additional Deduction",
        filters={
            "docstatus": 1,
            "ref_doctype": "Additional Salary",
            "ref_docname": ["in", additional_salary_list]
        },
        fields=["name"]
    )

    for d in additional_deductions:
        doc = frappe.get_doc("Additional Deduction", d.name)
        doc.cancel()


def validate_salary_slip_before_cancel(self):
    employees = list(set([
        row.employee for row in self.leave_settlement_deductions if row.employee
    ]))
    if not employees:
        return

    salary_slips = _find_overlapping_salary_slips(employees, self.date_of_settlement)
    if salary_slips:
        _throw_salary_slip_cancel_error(salary_slips, "Leave Settlement")


def _find_overlapping_salary_slips(employees, settlement_date):
    salary_slips = []
    for employee in employees:
        slips = frappe.get_all(
            "Salary Slip",
            filters={
                "employee": employee,
                "docstatus": 1,
                "start_date": ["<=", getdate(settlement_date)],
                "end_date": [">=", getdate(settlement_date)]
            },
            fields=["name", "employee", "employee_name", "start_date", "end_date"]
        )
        salary_slips.extend(slips)
    return salary_slips


def _throw_salary_slip_cancel_error(salary_slips, doc_type):
    message = f"""
    <b>Cannot Cancel {doc_type}</b>
    <br><br>
    Following submitted Salary Slips exist for the settlement date.
    Please cancel them first.
    <br><br>
    """
    for slip in salary_slips:
        message += f"""
        <li>
            <b>{slip.name}</b> - {slip.employee_name}
            ({slip.start_date} to {slip.end_date})
        </li>
        """
    frappe.throw(message)


def get_leave_period(company, settlement_date):
    leave_periods = frappe.get_all(
        "Leave Period",
        filters={
            "company": company,
            "from_date": ["<=", settlement_date],
            "to_date": [">=", settlement_date],
            "is_active": 1
        },
        fields=["name"],
        order_by="from_date desc",
        limit=1
    )
    return leave_periods[0].name if leave_periods else None
