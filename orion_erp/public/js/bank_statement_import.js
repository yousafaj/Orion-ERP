// Fallback for Bank Statement Import status updates.
//
// This deployment has no working realtime socket (browsers never connect to
// the socketio port), so `data_import_refresh` events never reach the UI and
// the status only updates on a manual page refresh. In developer mode the
// import runs synchronously inside the `form_start_import` request, so the
// status is already final once that call resolves — refresh the form then.
// For background (async) imports, poll the status as a fallback.

frappe.ui.form.off("Bank Statement Import", "start_import");

frappe.ui.form.on("Bank Statement Import", {
	start_import(frm) {
		frm.call({
			method: "form_start_import",
			args: { data_import: frm.doc.name },
			btn: frm.page.btn_primary,
		}).then((r) => {
			if (r.message === true) {
				frm.disable_save();
			}

			const refresh_doc = () => {
				frappe.model.clear_doc("Bank Statement Import", frm.doc.name);
				frappe.model.with_doc("Bank Statement Import", frm.doc.name).then(() => {
					frm.refresh();
				});
			};

			refresh_doc();

			let attempts = 0;
			const poll = () => {
				if (attempts++ > 60) return;
				setTimeout(() => {
					frappe.call({
						method: "erpnext.accounts.doctype.bank_statement_import.bank_statement_import.get_import_status",
						args: { docname: frm.doc.name },
						callback: (res) => {
							let status = res.message && res.message.status;
							if (status && status !== "Pending") {
								refresh_doc();
							} else {
								poll();
							}
						},
					});
				}, 2000);
			};
			poll();
		});
	},
});
