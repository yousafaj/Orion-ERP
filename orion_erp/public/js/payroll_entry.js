// Adds "Leave Pay" buttons to Payroll Entry (see orion_erp.leave_management.payroll)
const LEAVE_PAY = "orion_erp.leave_management.payroll.";

frappe.ui.form.on("Payroll Entry", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.docstatus === 2 || frm.doc.salary_slips_created) return;

		frm.add_custom_button(
			__("Preview Leave Deductions"),
			() => {
				if (frm.is_dirty()) return frappe.msgprint(__("Save the Payroll Entry first."));
				frappe.call({
					method: LEAVE_PAY + "preview_leave_deductions",
					args: { payroll_entry: frm.doc.name },
					freeze: true,
					callback(r) {
						const rows = r.message || [];
						if (!rows.length) {
							return frappe.msgprint(__("No half-pay or unpaid leave days fall in this period."));
						}
						const esc = frappe.utils.escape_html;
						const body = rows
							.map(
								(x) => `<tr><td>${esc(x.employee_name || x.employee)}</td><td>${esc(x.leave_type)}</td>
								<td>${x.pay_percent}%</td><td class="text-right">${x.days}</td>
								<td class="text-right">${format_currency(x.daily_rate)}</td>
								<td class="text-right">${format_currency(x.amount)}</td></tr>`
							)
							.join("");
						frappe.msgprint({
							title: __("Leave Deductions"),
							wide: true,
							message: `<table class="table table-bordered"><thead><tr><th>${__("Employee")}</th>
								<th>${__("Leave Type")}</th><th>${__("Pay")}</th><th>${__("Days")}</th>
								<th>${__("Daily Rate")}</th><th>${__("Deduction")}</th></tr></thead><tbody>${body}</tbody></table>`,
						});
					},
				});
			},
			__("Leave Pay")
		);

		frm.add_custom_button(
			__("Create Leave Deductions"),
			() => {
				if (frm.is_dirty()) return frappe.msgprint(__("Save the Payroll Entry first."));
				frappe.confirm(__("Create Additional Salary deductions for half-pay and unpaid leave in this period?"), () => {
					frappe.call({
						method: LEAVE_PAY + "create_leave_deductions",
						args: { payroll_entry: frm.doc.name },
						freeze: true,
						callback(r) {
							const m = r.message || {};
							let msg = __("Created: {0}, unchanged: {1}", [m.created, m.unchanged]);
							if ((m.blocked || []).length) msg += "<br><br>" + m.blocked.join("<br>");
							frappe.msgprint(msg);
						},
					});
				});
			},
			__("Leave Pay")
		);
	},
});
