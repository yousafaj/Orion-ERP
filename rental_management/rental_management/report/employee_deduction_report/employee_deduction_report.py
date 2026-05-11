# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
import re


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Deduction Doc",
            "fieldname": "parent",
            "fieldtype": "Link",
            "options": "Employee Deduction",
            "width": 180
        },
        {
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Penalty Type",
            "fieldname": "type_of_penalty",
            "fieldtype": "Link",
            "options": "Penalties",
            "width": 180
        },
        {
            "label": "Deduction Date",
            "fieldname": "deduction_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "Payroll Start",
            "fieldname": "payroll_start_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "Payroll End",
            "fieldname": "payrol_end_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "Amount",
            "fieldname": "deduction_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": "Paid Amount",
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": "Remaining",
            "fieldname": "remaining_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": "Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": "Remarks",
            "fieldname": "remarks",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Payroll Date",
            "fieldname": "additional_salary_date",
            "fieldtype": "Date",
            "width": 140
        },
    ]


def get_data(filters):

    conditions = ""
    values = {}

    if filters.get("employee"):
        conditions += " AND ed.employee = %(employee)s"
        values["employee"] = filters.get("employee")

    if filters.get("status"):
        conditions += " AND edd.status = %(status)s"
        values["status"] = filters.get("status")

    if filters.get("penalty_type"):
        conditions += " AND edd.type_of_penalty = %(penalty_type)s"
        values["penalty_type"] = filters.get("penalty_type")

    if filters.get("deduction_date"):
        conditions += " AND edd.deduction_date >= %(deduction_date)s"
        values["deduction_date"] = filters.get("deduction_date")

    if filters.get("payroll_start_date"):
        conditions += """
            AND edd.payroll_start_date >= %(payroll_start_date)s
        """
        values["payroll_start_date"] = (
            filters.get("payroll_start_date")
        )

    data = frappe.db.sql(
        f"""
        SELECT
            edd.name as edd_name,
            edd.parent,
            ed.employee,
            ed.employee_name,
            edd.type_of_penalty,
            edd.deduction_date,
            edd.payroll_start_date,
            edd.payrol_end_date,
            edd.deduction_amount,
            edd.installment_amount,
            edd.paid_amount,
            edd.remaining_amount,
            edd.status,
            edd.remarks,
            edd.reference

        FROM `tabEmployee Deduction Detail` edd

        INNER JOIN `tabEmployee Deduction` ed
            ON ed.name = edd.parent

        WHERE ed.docstatus = 1
        {conditions}

        ORDER BY
            ed.employee,
            edd.deduction_date
        """,
        values,
        as_dict=1
    )

    final_data = []

    for row in data:

        salary_list = []

        if row.get("reference"):

            salary_list = re.findall(
                r'>(HR-ADA-[^<]+)<',
                row.get("reference")
            )

        if not salary_list:

            row["additional_salary_date"] = ""

            final_data.append(row)

            continue


        total_amount = row.get("deduction_amount") or 0

        installment_amount = (
            row.get("installment_amount") or 0
        )

        running_paid = 0


        for idx, sal in enumerate(salary_list):

            try:

                sal_doc = frappe.get_doc(
                    "Additional Salary",
                    sal
                )

            except Exception:
                continue

            running_paid += installment_amount

            remaining_amount = (
                total_amount - running_paid
            )

            if remaining_amount <= 0:

                current_status = "Paid"

            else:

                current_status = "Partial Paid"

            if idx == 0:

                child_row = row.copy()

            else:

                child_row = {
                    "parent": "",
                    "employee": "",
                    "employee_name": "",
                    "type_of_penalty": "",
                    "deduction_date": "",
                    "payroll_start_date": "",
                    "payrol_end_date": "",
                    "deduction_amount": "",
                    "remarks": ""
                }

            # INSTALLMENT DETAILS
            child_row["paid_amount"] = (
                installment_amount
            )

            child_row["remaining_amount"] = (
                remaining_amount
            )

            child_row["status"] = (
                current_status
            )

            
            # PAYROLL DATE
            child_row["additional_salary_date"] = (
                sal_doc.payroll_date
            )

            final_data.append(child_row)

    return final_data