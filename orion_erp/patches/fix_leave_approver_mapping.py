import frappe


def execute():

    employees = frappe.get_all(

        "Employee",

        fields=[
            "name",
            "leave_approver",
            "custom_leave_approver_1",
            "custom_leave_approver_2",
            "custom_leave_approver_3",
            "custom_leave_approver_4"
        ]
    )

    for emp in employees:

        original_leave_approver = emp.leave_approver

        frappe.db.set_value(

            "Employee",

            emp.name,

            {

                "leave_approver":
                emp.custom_leave_approver_1,

                "custom_leave_approver_1":
                emp.custom_leave_approver_2,

                "custom_leave_approver_2":
                emp.custom_leave_approver_3,

                "custom_leave_approver_3":
                emp.custom_leave_approver_4,

                "custom_leave_approver_4":
                original_leave_approver
            }
        )