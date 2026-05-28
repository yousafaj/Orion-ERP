frappe.query_reports["Employee Deduction Report"] = {
    "filters": [

        {
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee"
        },

        {
            fieldname: "status",
            label: "Status",
            fieldtype: "Select",
            options: "\nUnpaid\nPartial Paid\nPaid"
        },

        {
            fieldname: "penalty_type",
            label: "Penalty Type",
            fieldtype: "Link",
            options: "Penalties"
        },

        {
            fieldname: "month",
            label: "Month",
            fieldtype: "Select",
            options: "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",

            on_change: function(report) {
                set_payroll_dates(report);
            }
        },

        {
            fieldname: "year",
            label: "Year",
            fieldtype: "Int",
            default: new Date().getFullYear(),

            on_change: function(report) {
                set_payroll_dates(report);
            }
        },

        {
            fieldname: "payroll_start_date",
            label: "Payroll Start >=",
            fieldtype: "Date"
        },

        {
            fieldname: "payroll_end_date",
            label: "Payroll End <=",
            fieldtype: "Date"
        },

        {
            fieldname: "deduction_date",
            label: "Deduction Date >=",
            fieldtype: "Date"
        }
    ]
};


function set_payroll_dates(report) {

    let month = report.get_filter_value("month");
    let year = report.get_filter_value("year");

    // CLEAR DATES IF MONTH EMPTY
    if (!month) {

        report.set_filter_value(
            "payroll_start_date",
            ""
        );

        report.set_filter_value(
            "payroll_end_date",
            ""
        );

        return;
    }

    if (!year) {
        return;
    }

    const month_map = {
        "January": 0,
        "February": 1,
        "March": 2,
        "April": 3,
        "May": 4,
        "June": 5,
        "July": 6,
        "August": 7,
        "September": 8,
        "October": 9,
        "November": 10,
        "December": 11
    };

    let month_index = month_map[month];

    let first_date = new Date(year, month_index, 1);

    let last_date = new Date(year, month_index + 1, 0);

    report.set_filter_value(
        "payroll_start_date",
        frappe.datetime.obj_to_str(first_date)
    );

    report.set_filter_value(
        "payroll_end_date",
        frappe.datetime.obj_to_str(last_date)
    );
}