// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Process Employee Deductions", {
        before_cancel(frm) {

            return new Promise((resolve, reject) => {

                frappe.confirm(
                    __(
                        "All related Additional Deductions will also be cancelled. Do you still want to cancel this document?"
                    ),

                    function () {
                        resolve();
                    },

                    function () {
                        reject();
                    }
                );

            });
        },
    refresh(frm) {
        set_current_fiscal_year(frm);
        let grid = frm.fields_dict.outstanding_installments.grid;

        // force search to appear even for 1 row
        grid.meta.rows_threshold_for_grid_search = 1;
        grid.cannot_add_rows = true;

        // disable delete row
        grid.cannot_delete_rows = true;
        // rebuild grid header
        grid.make_head();
        grid.refresh();
    },

    onload(frm) {
        set_current_fiscal_year(frm);
    },

    payroll_month(frm) {
        set_payroll_dates(frm);
        clear_outstanding_installments(frm);
    },

    year(frm) {
        if (frm.doc.payroll_month) {
            set_payroll_dates(frm);
        }
        clear_outstanding_installments(frm);
    },
    employee_category(frm) {
        clear_outstanding_installments(frm);
    }
});
function clear_outstanding_installments(frm) {

    frm.clear_table("outstanding_installments");

    frm.refresh_field("outstanding_installments");
}
frappe.ui.form.on("Process Employee Deduction Detail", {
    form_render(frm, cdt, cdn) {

        setTimeout(() => {

            // hide delete button inside row form
            $('.grid-delete-row').hide();

            // hide insert below/above
            $('.grid-insert-row-below').hide();
            $('.grid-insert-row').hide();

        }, 100);
    }
});
function set_current_fiscal_year(frm) {
    if (!frm.doc.year) {
        frappe.call({
            method: "erpnext.accounts.utils.get_fiscal_year",
            args: {
                date: frappe.datetime.get_today()
            },
            callback: function(r) {
                if (r.message && r.message[0]) {
                    frm.set_value("year", r.message[0]);
                }
            }
        });
    }
}

function set_payroll_dates(frm) {

    if (!frm.doc.payroll_month || !frm.doc.year) {
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

    let fiscal_year = frm.doc.year;

    // Extract year like 2026 from "2026-2027"
    let start_year = parseInt(fiscal_year.split("-")[0]);

    let month_index = month_map[frm.doc.payroll_month];

    // Jan-Mar belong to next calendar year in Indian fiscal year
    let actual_year = month_index <= 2 ? start_year + 1 : start_year;

    let first_date = new Date(actual_year, month_index, 1);

    let last_date = new Date(actual_year, month_index + 1, 0);

    frm.set_value(
        "payroll_start_date",
        frappe.datetime.obj_to_str(first_date)
    );

    frm.set_value(
        "payroll_date_date",
        frappe.datetime.obj_to_str(last_date)
    );
}