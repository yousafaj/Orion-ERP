import frappe
from frappe import _
from frappe.utils import flt, getdate


def validate_duplicate_transaction(self):
    exists = frappe.db.exists(
        "Process Employee Deductions",
        {
            "name": ["!=", self.name],
            "docstatus": ["!=", 2],
            "year": self.year,
            "payroll_month": self.payroll_month,
            "employee_category": self.employee_category
        }
    )
    if exists:
        frappe.throw(
            f"Process Employee Deductions already exists for "
            f"Employee Category <b>{self.employee_category}</b>, "
            f"Month <b>{self.payroll_month}</b> "
            f"and Fiscal Year <b>{self.year}</b>"
        )


def populate_outstanding_installments(self):
    self.outstanding_installments = []

    employees = frappe.get_all(
        "Employee",
        filters={"custom_employee_category": self.employee_category},
        fields=["name", "employee_name"]
    )

    for emp in employees:
        _populate_for_employee(self, emp)


def _populate_for_employee(self, emp):
    parent = frappe.get_all(
        "Employee Deduction",
        filters={"employee": emp.name, "docstatus": 1},
        fields=["name"],
        order_by="creation desc",
        limit=1
    )
    if not parent:
        return

    doc = frappe.get_doc("Employee Deduction", parent[0].name)

    for row in doc.employee_deduction_detail or []:
        if _is_installment_applicable(row, self.payroll_date_date):
            installment_amount = min(row.installment_amount, row.remaining_amount)
            self.append("outstanding_installments", _build_installment_row(doc, row, installment_amount))

    for row in doc.outstanding_employee_deduction_detail or []:
        if _is_installment_applicable(row, self.payroll_date_date):
            installment_amount = min(row.installment_amount, row.remaining_amount)
            self.append("outstanding_installments", _build_installment_row(doc, row, installment_amount))


def _is_installment_applicable(row, payroll_date_date):
    return flt(row.remaining_amount) > 0 and getdate(row.payroll_start_date) <= getdate(payroll_date_date)


def _build_installment_row(doc, row, installment_amount):
    return {
        "employee": doc.employee,
        "employee_name": doc.employee_name,
        "type_of_penalty": row.type_of_penalty,
        "date_of_deduction_occurred": row.deduction_date,
        "outstanding_amount": row.remaining_amount,
        "installment_amount": installment_amount,
        "employee_deduction_reference": row.name,
        "employee_deduction_parent_reference": row.parent,
        "amount_to_be_deducted_this_month": installment_amount
    }


def fetch_new_deductions(self):
    existing_child_refs = _get_existing_child_refs(self)

    employees = frappe.get_all(
        "Employee",
        filters={"custom_employee_category": self.employee_category},
        fields=["name", "employee_name"]
    )

    for emp in employees:
        _fetch_deductions_for_employee(self, emp, existing_child_refs)


def _get_existing_child_refs(self):
    return {
        row.employee_deduction_reference
        for row in self.outstanding_installments
        if row.employee_deduction_reference
    }


def _fetch_deductions_for_employee(self, emp, existing_child_refs):
    parent = frappe.get_all(
        "Employee Deduction",
        filters={"employee": emp.name, "docstatus": 1},
        fields=["name"],
        order_by="creation desc",
        limit=1
    )
    if not parent:
        return

    doc = frappe.get_doc("Employee Deduction", parent[0].name)

    for row in doc.employee_deduction_detail or []:
        if _is_new_deduction_applicable(row, self, existing_child_refs):
            installment_amount = min(row.installment_amount, row.remaining_amount)
            self.append("outstanding_installments", _build_installment_row(doc, row, installment_amount))

    for row in doc.outstanding_employee_deduction_detail or []:
        if _is_new_deduction_applicable(row, self, existing_child_refs):
            installment_amount = min(row.installment_amount, row.remaining_amount)
            self.append("outstanding_installments", _build_installment_row(doc, row, installment_amount))


def _is_new_deduction_applicable(row, self, existing_child_refs):
    return (
        flt(row.remaining_amount) > 0
        and getdate(row.payroll_start_date) >= getdate(self.payroll_start_date)
        and getdate(row.payroll_start_date) <= getdate(self.payroll_date_date)
        and row.name not in existing_child_refs
    )


@frappe.whitelist()
def get_new_deductions_for_process(docname):
    if not docname or not frappe.db.exists("Process Employee Deductions", docname):
        return []

    doc = frappe.get_doc("Process Employee Deductions", docname)
    if doc.docstatus != 0:
        return []

    existing_child_refs = _get_existing_child_refs(doc)
    new_rows = []

    employees = frappe.get_all(
        "Employee",
        filters={"custom_employee_category": doc.employee_category},
        fields=["name", "employee_name"]
    )

    for emp in employees:
        rows = _collect_new_deduction_rows(doc, emp, existing_child_refs)
        new_rows.extend(rows)

    return new_rows


def _collect_new_deduction_rows(doc, emp, existing_child_refs):
    parent = frappe.get_all(
        "Employee Deduction",
        filters={"employee": emp.name, "docstatus": 1},
        fields=["name"],
        order_by="creation desc",
        limit=1
    )
    if not parent:
        return []

    ed = frappe.get_doc("Employee Deduction", parent[0].name)
    rows = []

    for row in ed.employee_deduction_detail or []:
        if _is_new_deduction_applicable(row, doc, existing_child_refs):
            installment_amount = min(row.installment_amount, row.remaining_amount)
            rows.append(_build_installment_row(ed, row, installment_amount))

    for row in ed.outstanding_employee_deduction_detail or []:
        if _is_new_deduction_applicable(row, doc, existing_child_refs):
            installment_amount = min(row.installment_amount, row.remaining_amount)
            rows.append(_build_installment_row(ed, row, installment_amount))

    return rows


def process_create_additional_salary(self):
    employee_wise_data = _group_rows_by_employee(self)

    for employee, rows in employee_wise_data.items():
        _create_salary_for_employee(self, employee, rows)


def _group_rows_by_employee(self):
    data = {}
    for row in self.outstanding_installments:
        if row.skip_penalty_amount or not row.employee:
            continue
        if flt(row.amount_to_be_deducted_this_month) <= 0:
            continue
        data.setdefault(row.employee, []).append(row)
    return data


def _create_salary_for_employee(self, employee, rows):
    total_amount = sum(flt(d.amount_to_be_deducted_this_month) for d in rows)
    if total_amount <= 0:
        return

    _check_existing_additional_salary(self, employee)

    employee_doc = frappe.get_doc("Employee", employee)
    additional_salary = frappe.new_doc("Additional Salary")
    additional_salary.employee = employee
    additional_salary.company = employee_doc.company
    additional_salary.payroll_date = self.payroll_date_date
    additional_salary.salary_component = "Total Deduction"
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

    additional_salary.insert(ignore_permissions=True)
    additional_salary.submit()

    for d in rows:
        d.db_set("additional_salary_ref", additional_salary.name, update_modified=False)


def _check_existing_additional_salary(self, employee):
    existing_salary = frappe.db.exists(
        "Additional Salary",
        {
            "employee": employee,
            "payroll_date": self.payroll_date_date,
            "salary_component": "Total Deduction",
            "overwrite_salary_structure_amount": 1,
            "docstatus": ["!=", 2]
        }
    )
    if existing_salary:
        link = frappe.utils.get_link_to_form("Additional Salary", existing_salary)
        frappe.throw(
            f"<b>Additional Salary Already Exists</b><br><br>"
            f"System found an existing Additional Salary for:<br><br>"
            f"Employee: <b>{employee}</b><br>"
            f"Payroll Date: <b>{self.payroll_date_date}</b><br><br>"
            f"Please cancel the existing Additional Salary first.<br><br>"
            f"Reference: {link}"
        )


def validate_salary_slip_before_cancel(self):
    employees = list(set([
        row.employee for row in self.outstanding_installments if row.employee
    ]))
    if not employees:
        return

    salary_slips = []
    for employee in employees:
        slips = frappe.get_all(
            "Salary Slip",
            filters={
                "employee": employee,
                "docstatus": 1,
                "start_date": ["<=", getdate(self.payroll_date_date)],
                "end_date": [">=", getdate(self.payroll_start_date)]
            },
            fields=["name", "employee", "employee_name", "start_date", "end_date"]
        )
        salary_slips.extend(slips)

    if salary_slips:
        _throw_cancel_error(salary_slips, "Process Employee Deduction")


def validate_salary_slip_exists(self):
    employees = list(set([
        row.employee for row in self.outstanding_installments if row.employee
    ]))
    if not employees:
        return

    salary_slips = []
    for employee in employees:
        slips = frappe.get_all(
            "Salary Slip",
            filters={
                "employee": employee,
                "docstatus": 1,
                "start_date": ["<=", getdate(self.payroll_date_date)],
                "end_date": [">=", getdate(self.payroll_start_date)]
            },
            fields=["name", "employee", "employee_name", "start_date", "end_date"]
        )
        salary_slips.extend(slips)

    if salary_slips:
        _throw_exists_error(salary_slips, self)


def _throw_cancel_error(salary_slips, doc_type):
    message = f"""
    <b>Cannot Cancel {doc_type}</b>
    <br><br>
    Following submitted Salary Slips exist for the selected payroll period.
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


def _throw_exists_error(salary_slips, self):
    message = f"""
    <b>Salary Slips Already Exist</b>
    <br><br>
    Salary Slips are already created for the selected payroll period:
    <br><b>{self.payroll_start_date} to {self.payroll_date_date}</b>
    <br><br>
    Please cancel the below Salary Slips first, then submit this document.
    <br><br>
    """
    for slip in salary_slips:
        message += f"""
        <li>
            <b>{slip.name}</b> - {slip.employee_name}
            <br>Payroll Period: {slip.start_date} to {slip.end_date}
        </li>
        """
    frappe.throw(message)


def cancel_linked_additional_deductions(self):
    additional_salary_list = list(set([
        row.additional_salary_ref
        for row in self.outstanding_installments
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
