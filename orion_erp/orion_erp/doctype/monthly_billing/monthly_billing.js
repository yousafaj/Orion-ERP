// Copyright (c) 2026, Orion ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Monthly Billing", {
	refresh(frm) {
		// Refresh the billable lines from current data — available until invoiced
		// (the sheet also auto-rebuilds on every save).
		if (!frm.is_new() && frm.doc.docstatus !== 2 && !frm.doc.invoiced) {
			frm.add_custom_button(__("Refresh Lines"), () => {
				frappe.call({
					method: "orion_erp.orion_erp.doctype.monthly_billing.monthly_billing.build",
					args: { name: frm.doc.name },
					freeze: true,
					freeze_message: __("Refreshing…"),
					callback: () => frm.reload_doc(),
				});
			});
		}

		// Mark as Invoiced — Accounts only, on a submitted, not-yet-invoiced sheet.
		const is_accounts =
			frappe.user.has_role("Accounts Manager") || frappe.user.has_role("System Manager");
		if (frm.doc.docstatus === 1 && !frm.doc.invoiced && is_accounts) {
			frm.add_custom_button(__("Mark as Invoiced"), () => {
				frappe.prompt(
					[
						{
							fieldname: "invoiced_date",
							label: __("Invoiced On"),
							fieldtype: "Date",
							reqd: 1,
							default: frappe.datetime.get_today(),
						},
						{
							fieldname: "external_invoice_ref",
							label: __("External Invoice Ref"),
							fieldtype: "Data",
							reqd: 1,
						},
					],
					(values) => {
						frappe.call({
							method: "orion_erp.orion_erp.doctype.monthly_billing.monthly_billing.mark_invoiced",
							args: {
								name: frm.doc.name,
								invoiced_date: values.invoiced_date,
								external_invoice_ref: values.external_invoice_ref,
							},
							freeze: true,
							callback: () => frm.reload_doc(),
						});
					},
					__("Mark Month as Invoiced"),
					__("Confirm")
				);
			}).addClass("btn-primary");
		}
	},
});
