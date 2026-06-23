// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

function populate_leave_pay(frm) {
    if (!frm.doc.employee || !frm.doc.date_of_settlement) {
        frm.clear_table("leave_pay");
        frm.refresh_field("leave_pay");
        return;
    }

    if (frm.doc.type_of_settlement !== "Final Settlement") {
        frm.clear_table("leave_pay");
        frm.refresh_field("leave_pay");
        return;
    }

    frappe.call({
        method: "orion_erp.orion_erp.doctype.leave_settlement.leave_settlement.get_leave_pay_data",
        args: {
            employee: frm.doc.employee,
            date_of_settlement: frm.doc.date_of_settlement,
            doj: frm.doc.doj__re_joining_date
        },
        callback: function(r) {

            frm.clear_table("leave_pay");

            if (!r.message || !r.message.length) {
                frm.refresh_field("leave_pay");
                return;
            }

            r.message.forEach(row => {

                let d = frm.add_child("leave_pay");

                d.leave_type = row.leave_type;
                d.from = row.from;
                d.to = row.to;
                d.tenure = row.tenure;
                d.amount = row.amount;

            });

            frm.refresh_field("leave_pay");
        }
    });
}

function set_delete_buttons_visibility(frm) {
    let is_final = frm.doc.type_of_settlement === "Final Settlement";

    let grid = frm.fields_dict.ticket_allowance.grid;
    grid.cannot_add_rows = true;
    grid.cannot_delete_rows = is_final;

    let leave_deduction_grid = frm.fields_dict.leave_settlement_deductions.grid;
    leave_deduction_grid.cannot_add_rows = true;
    leave_deduction_grid.cannot_delete_rows = is_final;

    let leave_pay_grid = frm.fields_dict.leave_pay.grid;
    leave_pay_grid.cannot_add_rows = true;
    leave_pay_grid.cannot_delete_rows = is_final;

    setTimeout(() => {
        let ta_grid = frm.fields_dict.ticket_allowance.grid;
        ta_grid.wrapper.find('.grid-remove-rows').toggle(!is_final);
        ta_grid.wrapper.find('.grid-checkbox').toggle(!is_final);

        let ls_grid = frm.fields_dict.leave_settlement_deductions.grid;
        ls_grid.wrapper.find('.grid-remove-rows').toggle(!is_final);
        ls_grid.wrapper.find('.grid-checkbox').toggle(!is_final);

        let lp_grid = frm.fields_dict.leave_pay.grid;
        lp_grid.wrapper.find('.grid-remove-rows').toggle(!is_final);
        lp_grid.wrapper.find('.grid-checkbox').toggle(!is_final);
    }, 200);
}

frappe.ui.form.on('Leave Settlement', {
    refresh(frm) {
        set_delete_buttons_visibility(frm);

        frm.refresh_field("ticket_allowance");
        frm.refresh_field("leave_settlement_deductions");
        frm.refresh_field("leave_pay");
    },
    date_of_settlement:function(frm) {
        fetch_ticket_allowance(frm);
        populate_leave_pay(frm);
    },
    type_of_settlement: function(frm) {

        const deduction_allowed_types = [
            "Vacation Settlement",
            "Final Settlement"
        ];

        if (
            deduction_allowed_types.includes(
                frm.doc.type_of_settlement
            )
        ) {
            frm.call(
                "populate_leave_settlement_deductions"
            ).then(() => {
                frm.refresh_field("leave_settlement_deductions");
            });
        } else {
            frm.clear_table("leave_settlement_deductions");
            frm.refresh_field("leave_settlement_deductions");
        }
        fetch_ticket_allowance(frm);
        populate_leave_pay(frm);
        set_delete_buttons_visibility(frm);
    },
    employee: function(frm) {
        const deduction_allowed_types = [
            "Vacation Settlement",
            "Final Settlement"
        ];

        if (!frm.doc.employee) {
            frm.clear_table("leave_settlement_deductions");
            frm.refresh_field("leave_settlement_deductions");
            frm.clear_table("leave_pay");
            frm.refresh_field("leave_pay");
            return;
        }

        let after_deductions = function() {
            fetch_ticket_allowance(frm);
            populate_leave_pay(frm);
        };

        if (
            deduction_allowed_types.includes(
                frm.doc.type_of_settlement
            )
        ) {
            frm.call(
                "populate_leave_settlement_deductions"
            ).then(() => {
                frm.refresh_field("leave_settlement_deductions");
                after_deductions();
            });
        } else {
            frm.clear_table("leave_settlement_deductions");
            frm.refresh_field("leave_settlement_deductions");
            after_deductions();
        }

        frappe.db.get_doc('Employee', frm.doc.employee).then(emp => {

            let monthly_salary =
                flt(emp.custom_basic) +
                flt(emp.custom_food_allowances_fa) +
                flt(emp.custom_house_rent_allowances) +
                flt(emp.custom_other_allowances) +
                flt(emp.custom_transporatation_allowances);

            frm.set_value("monthly_salary", monthly_salary);
        });

    },
    last_working_day: function(frm) {
        calculate_total_service(frm);
    },

    doj__re_joining_date: function(frm) {
        calculate_total_service(frm);
    },
    validate: function(frm) {

            let total_entitlements = 0;
            let total_deductions = 0;

            function sum_table(table) {

                let total = 0;

                (table || []).forEach(row => {

                    total += flt(row.amount);
                });

                return total;
            }

            // CHILD TABLE TOTALS
            total_entitlements += sum_table(
                frm.doc.salary_due
            );

            total_entitlements += sum_table(
                frm.doc.leave_pay
            );

            total_entitlements += sum_table(
                frm.doc.gratuity_pay
            );

            total_entitlements += sum_table(
                frm.doc.ticket_allowance
            );

            // ADDITIONAL ALLOWANCES
            total_entitlements += flt(
                frm.doc.overtime_allowance
            );

            total_entitlements += flt(
                frm.doc.other_allowance
            );

            // DEDUCTIONS
            total_deductions += flt(
                frm.doc.outstanding_advance
            );

            total_deductions += flt(
                frm.doc.traffic_fine
            );

            total_deductions += flt(
                frm.doc.adjustments
            );

            total_deductions += flt(
                frm.doc.other_deduction
            );

            // LEAVE SETTLEMENT DEDUCTIONS
            (frm.doc.leave_settlement_deductions || []).forEach(row => {

                total_deductions += flt(
                    row.amount_to_be_deducted_this_month
                );
            });

            
            // SET VALUES
            frm.set_value(
                "total_entitlements",
                total_entitlements
            );

            frm.set_value(
                "total_deductions",
                total_deductions
            );

            frm.set_value(
                "total_settlement_payable",
                total_entitlements - total_deductions
            );
        }
});

function calculate_total_service(frm) {

    if(frm.doc.last_working_day && frm.doc.doj__re_joining_date){

        let start = frappe.datetime.str_to_obj(frm.doc.doj__re_joining_date);
        let end = frappe.datetime.str_to_obj(frm.doc.last_working_day);

        let diff_days = frappe.datetime.get_day_diff(end, start);

        let total_service = (diff_days / 30).toFixed(1);

        frm.set_value("total_service", total_service);
    }
}
frappe.ui.form.on('Salary Due', {
    from: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    },
    to: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Leave Pay', {
    from: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    },
    to: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    },
    tenure: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.leave_type && row.tenure) {
            frappe.db.get_value('Employee', frm.doc.employee, 'custom_total_salary_as_per_offer_letter', (r) => {
                let offer_salary = flt(r.custom_total_salary_as_per_offer_letter) || 0;
                if (offer_salary > 0) {
                    let amount = (offer_salary / 30) * flt(row.tenure);
                    frappe.model.set_value(cdt, cdn, "amount", amount);
                }
            });
        }
    }
});

frappe.ui.form.on('Ticket Allowance', {
    from: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    },
    to: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Gratuity Pay', {
    from: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    },
    to: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    }
});

function calculate_row(frm, cdt, cdn){

    let row = locals[cdt][cdn];

    if(row.from && row.to){

        // calculate duration
        let duration = frappe.datetime.get_day_diff(row.to, row.from) + 1;

        if("days" in row){
            frappe.model.set_value(cdt, cdn, "days", duration);
        }
        if("tenure" in row && !row.leave_type){
            frappe.model.set_value(cdt, cdn, "tenure", duration);
        }

        // get days in month
        let d = new Date(row.from);
        let month_days = new Date(d.getFullYear(), d.getMonth()+1, 0).getDate();

        // calculate amount (skip for auto-populated leave pay rows)
        if (!row.leave_type) {
            let amount = (flt(frm.doc.monthly_salary) / month_days) * duration;
            frappe.model.set_value(cdt, cdn, "amount", amount);
        }
    }
}

function fetch_ticket_allowance(frm) {


    if (!frm.doc.employee) {
        return;
    }

    if (!frm.doc.date_of_settlement) {
        return;
    }

    const allowed_types = [
        "Vacation Settlement",
        "Final Settlement",
        "Internal Transfer Settlement"
    ];


    if (
        !allowed_types.includes(
            frm.doc.type_of_settlement
        )
    ) {

        frm.clear_table("ticket_allowance");

        frm.refresh_field(
            "ticket_allowance"
        );

        return;
    }

    frappe.call({

        method: "orion_erp.orion_erp.doctype.leave_settlement.leave_settlement.get_ticket_allowance",

        args: {
            employee: frm.doc.employee,
            settlement_date: frm.doc.date_of_settlement
        },

        callback: function(r) {

            frm.clear_table("ticket_allowance");
            
            if (!r.message || !r.message.length) {

                frm.refresh_field(
                    "ticket_allowance"
                );

                return;
            }

            r.message.forEach(row => {

                let d = frm.add_child(
                    "ticket_allowance"
                );
                
                d.from = row.from;
                d.to = row.to;
                d.amount = row.amount;

            });

            frm.refresh_field(
                "ticket_allowance"
            );
        }
    });
}

frappe.ui.form.on("Ticket Allowance", {
    form_render(frm, cdt, cdn) {

        setTimeout(() => {
            let is_final = frm.doc.type_of_settlement === "Final Settlement";
            $('.grid-delete-row').toggle(!is_final);
            $('.grid-insert-row-below').toggle(!is_final);
            $('.grid-insert-row').toggle(!is_final);
        }, 100);
    }
});

frappe.ui.form.on("Leave Pay", {
    form_render(frm, cdt, cdn) {

        setTimeout(() => {
            let is_final = frm.doc.type_of_settlement === "Final Settlement";
            $('.grid-delete-row').toggle(!is_final);
            $('.grid-insert-row').toggle(!is_final);
            $('.grid-insert-row-below').toggle(!is_final);
        }, 100);
    }
});

frappe.ui.form.on("Leave Settlement Deductions", {
    form_render(frm, cdt, cdn) {

		setTimeout(() => {
            let is_final = frm.doc.type_of_settlement === "Final Settlement";
			$('.grid-delete-row').toggle(!is_final);
			$('.grid-insert-row').toggle(!is_final);
			$('.grid-insert-row-below').toggle(!is_final);
		}, 100);
	},
	amount_to_be_deducted_this_month(frm, cdt, cdn) {

		let row = locals[cdt][cdn];


		if (
			flt(row.amount_to_be_deducted_this_month) < 0
		) {

			frappe.model.set_value(
				cdt,
				cdn,
				"amount_to_be_deducted_this_month",
				0
			);

			frappe.throw(
				__(
					"Amount To Be Deducted This Month cannot be less than 0"
				)
			);
		}

		if (
			flt(row.amount_to_be_deducted_this_month) >
			flt(row.outstanding_amount)
		) {

			frappe.model.set_value(
				cdt,
				cdn,
				"amount_to_be_deducted_this_month",
				row.outstanding_amount
			);

			frappe.throw(
				__(
					"Amount To Be Deducted This Month cannot be greater than Outstanding Amount"
				)
			);
		}
	}

});