// // Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// // For license information, please see license.txt

// // frappe.query_reports["UAE VAT 201 Orion"] = {
// // 	filters: [
// // 		{
// // 			fieldname: "company",
// // 			label: __("Company"),
// // 			fieldtype: "Link",
// // 			options: "Company",
// // 			reqd: 1,
// // 			default: frappe.defaults.get_user_default("Company"),
// // 		},
// // 		{
// // 			fieldname: "from_date",
// // 			label: __("From Date"),
// // 			fieldtype: "Date",
// // 			reqd: 1,
// // 			default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
// // 		},
// // 		{
// // 			fieldname: "to_date",
// // 			label: __("To Date"),
// // 			fieldtype: "Date",
// // 			reqd: 1,
// // 			default: frappe.datetime.get_today(),
// // 		},
// // 		{
// // 			fieldname: "drilldown_key",
// // 			fieldtype: "Data",
// // 			hidden: 1,
// // 		},
// // 	],

// // 	open_drilldown: function (key) {
// // 		if (!key) return;
// // 		frappe.query_report.set_filter_value({ drilldown_key: key });
// // 		frappe.query_report.page.set_primary_action(__("Back to Summary"), function () {
// // 			frappe.query_report.set_filter_value({ drilldown_key: "" });
// // 			frappe.query_report.page.clear_primary_action();
// // 		});
// // 	},

// // 	onload: function (report) {
// // 		if (report.get_filter_value("drilldown_key")) {
// // 			report.page.set_primary_action(__("Back to Summary"), function () {
// // 				frappe.query_report.set_filter_value({ drilldown_key: "" });
// // 				report.page.clear_primary_action();
// // 			});
// // 		}
// // 	},

// // 	formatter: function (value, row, column, data, default_formatter) {
// // 		// In drilldown mode, just render normally
// // 		if (frappe.query_report.get_filter_value("drilldown_key")) {
// // 			return default_formatter(value, row, column, data);
// // 		}

// // 		// Make amount/vat_amount clickable links for drill-down
// // 		if (
// // 			data &&
// // 			data.drilldown_key &&
// // 			(column.fieldname === "amount" || column.fieldname === "vat_amount") &&
// // 			data["raw_" + column.fieldname] !== 0 &&
// // 			value &&
// // 			value !== "-"
// // 		) {
// // 			var formatted = default_formatter(value, row, column, data);
// // 			var onclick =
// // 				"frappe.query_reports['UAE VAT 201 Orion'].open_drilldown('" +
// // 				data.drilldown_key +
// // 				"')";
// // 			return (
// // 				'<a onclick="' +
// // 				onclick +
// // 				'" ' +
// // 				'style="text-decoration:underline;cursor:pointer;">' +
// // 				formatted +
// // 				"</a>"
// // 			);
// // 		}

// // 		// Bold section headers and totals
// // 		if (
// // 			data &&
// // 			(data.legend == "VAT on Sales and All Other Outputs" ||
// // 				data.legend == "VAT on Expenses and All Other Inputs" ||
// // 				data.legend == "Total VAT on Sales and All Other Outputs" ||
// // 				data.legend == "Total VAT on Expenses and All Other Inputs") &&
// // 			data.legend == value
// // 		) {
// // 			value = $(`<span>${value}</span>`);
// // 			var $value = $(value).css("font-weight", "bold");
// // 			value = $value.wrap("<p></p>").parent().html();
// // 		}
// // 		return value;
// // 	},
// // };





// /////////////////////////////////////////////////////////////////



// frappe.query_reports["UAE VAT 201 Orion"] = {
// 	filters: [
// 		{
// 			fieldname: "company",
// 			label: __("Company"),
// 			fieldtype: "Link",
// 			options: "Company",
// 			reqd: 1,
// 			default: frappe.defaults.get_user_default("Company"),
// 		},
// 		{
// 			fieldname: "from_date",
// 			label: __("From Date"),
// 			fieldtype: "Date",
// 			reqd: 1,
// 			default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
// 		},
// 		{
// 			fieldname: "to_date",
// 			label: __("To Date"),
// 			fieldtype: "Date",
// 			reqd: 1,
// 			default: frappe.datetime.get_today(),
// 		},
// 		{
// 			fieldname: "drilldown_key",
// 			fieldtype: "Data",
// 			hidden: 1,
// 		},
// 	],
 
// 	open_drilldown: function (key) {
// 		if (!key) return;
// 		frappe.query_report.set_filter_value({ drilldown_key: key });
// 		frappe.query_report.page.set_primary_action(__("Back to Summary"), function () {
// 			frappe.query_report.set_filter_value({ drilldown_key: "" });
// 			frappe.query_report.page.clear_primary_action();
// 		});
// 	},
 
// 	onload: function (report) {
// 		if (report.get_filter_value("drilldown_key")) {
// 			report.page.set_primary_action(__("Back to Summary"), function () {
// 				frappe.query_report.set_filter_value({ drilldown_key: "" });
// 				report.page.clear_primary_action();
// 			});
// 		}
 
// 		// NEW: "See Transactions" button
// 		report.page.add_inner_button(__("File VAT Return"), function () {
// 			open_vat_review(report);
// 		});
// 	},
 
// 	formatter: function (value, row, column, data, default_formatter) {
// 		// In drilldown mode, just render normally
// 		if (frappe.query_report.get_filter_value("drilldown_key")) {
// 			return default_formatter(value, row, column, data);
// 		}
 
// 		// Make amount/vat_amount clickable links for drill-down
// 		if (
// 			data &&
// 			data.drilldown_key &&
// 			(column.fieldname === "amount" || column.fieldname === "vat_amount") &&
// 			data["raw_" + column.fieldname] !== 0 &&
// 			value &&
// 			value !== "-"
// 		) {
// 			var formatted = default_formatter(value, row, column, data);
// 			var onclick =
// 				"frappe.query_reports['UAE VAT 201 Orion'].open_drilldown('" +
// 				data.drilldown_key +
// 				"')";
// 			return (
// 				'<a onclick="' +
// 				onclick +
// 				'" ' +
// 				'style="text-decoration:underline;cursor:pointer;">' +
// 				formatted +
// 				"</a>"
// 			);
// 		}
 
// 		// Bold section headers and totals
// 		if (
// 			data &&
// 			(data.legend == "VAT on Sales and All Other Outputs" ||
// 				data.legend == "VAT on Expenses and All Other Inputs" ||
// 				data.legend == "Total VAT on Sales and All Other Outputs" ||
// 				data.legend == "Total VAT on Expenses and All Other Inputs") &&
// 			data.legend == value
// 		) {
// 			value = $(`<span>${value}</span>`);
// 			var $value = $(value).css("font-weight", "bold");
// 			value = $value.wrap("<p></p>").parent().html();
// 		}
// 		return value;
// 	},
// };
 
// // =====================================================================
// // NEW: "See Transactions" review screen (everything below is new)
// // =====================================================================
 
// function open_vat_review(report) {
// 	const f = report.get_values();
// 	if (!f || !f.company || !f.from_date || !f.to_date) {
// 		frappe.msgprint(__("Please set Company, From Date and To Date first."));
// 		return;
// 	}
 
// 	// Runs the report itself with a special key (see get_vat_transactions in the .py)
// 	frappe.call({
// 		method: "frappe.desk.query_report.run",
// 		args: {
// 			report_name: "UAE VAT 201 Orion",
// 			filters: {
// 				company: f.company,
// 				from_date: f.from_date,
// 				to_date: f.to_date,
// 				drilldown_key: "vat_transactions",
// 			},
// 			ignore_prepared_report: true,
// 		},
// 		freeze: true,
// 		freeze_message: __("Loading transactions..."),
// 		callback(r) {
// 			if (r.message) show_vat_review(r.message.result || [], f);
// 		},
// 	});
// }
 
// function show_vat_review(rows, f) {
// 	const esc = frappe.utils.escape_html;
// 	const cur = frappe.boot.sysdefaults.currency || "AED";
// 	const money = (v) => format_currency(v, cur);
// 	const user_date = (d) => frappe.datetime.str_to_user(d);
 
// 	const current = rows.filter((r) => r.section === "current");
// 	const previous = rows.filter((r) => r.section === "previous");
// 	const lb_from = frappe.datetime.add_months(f.from_date, -3);
// 	const lb_to = frappe.datetime.add_days(f.from_date, -1);
 
// 	// Current-period items start ticked. Previous-period items must be approved by the user.
// 	const selected = new Set(current.filter((r) => !r.locked).map((r) => r.key));
 
// 	const d = new frappe.ui.Dialog({
// 		title: __("VAT Return Review"),
// 		size: "extra-large",
// 		fields: [{ fieldtype: "HTML", fieldname: "body" }],
// 	});
 
// 	const row = (r) => {
// 		const badge = r.type === "Sales" ? "vtx-badge-sales" : "vtx-badge-purchase";
// 		const note = r.note
// 			? `<span class="vtx-note ${r.locked ? "vtx-note-locked" : ""}">${esc(r.note)}</span>`
// 			: "";
// 		return `
// 		<label class="vtx-row ${r.locked ? "locked" : ""}" data-key="${esc(r.key)}">
// 			<input type="checkbox" ${r.locked ? "disabled" : ""} ${selected.has(r.key) ? "checked" : ""}>
// 			<div class="vtx-row-main">
// 				<div class="vtx-row-top">
// 					<a class="vtx-link" href="${esc(frappe.utils.get_form_link(r.doc_type, r.doc_name))}" target="_blank">${esc(r.doc_name)}</a>
// 					<span class="vtx-badge ${badge}">${esc(__(r.type))}</span>
// 					<span class="vtx-note">${esc(r.category)}</span>
// 					${note}
// 				</div>
// 				<div class="vtx-meta">${esc(r.doc_type)} · ${user_date(r.posting_date)} · ${esc(r.party)} · ${__("Amount")} ${money(r.amount)}</div>
// 			</div>
// 			<div class="vtx-amt">${money(r.vat)}</div>
// 		</label>`;
// 	};
 
// 	const section = (num, title, sub, list, banner) => `
// 		<section class="vtx-sec">
// 			<div class="vtx-sec-h">
// 				<div>
// 					<h5><span class="vtx-num">${num}</span>${title}</h5>
// 					<p>${sub}</p>
// 				</div>
// 				<span class="vtx-count" data-count-for="${num}"></span>
// 			</div>
// 			${banner || ""}
// 			<div class="vtx-list">
// 				${list.length ? list.map(row).join("") : `<div class="vtx-empty">${__("No transactions found")}</div>`}
// 			</div>
// 		</section>`;
 
// 	const html = `
// 	<style>${VAT_CSS}</style>
// 	<div class="vtx">
// 		<div class="vtx-head">
// 			<div class="vtx-card"><small>${__("Company")}</small><b>${esc(f.company)}</b></div>
// 			<div class="vtx-card"><small>${__("VAT period")}</small>
// 				<b>${user_date(f.from_date)} – ${user_date(f.to_date)}</b></div>
// 		</div>
// 		<div class="vtx-layout">
// 			<div class="vtx-main">
// 				${section(1, __("Current VAT-period transactions"),
// 					__("Eligible transactions from the selected filing period."), current)}
// 				${section(2, __("Previous-period transactions"),
// 					__("Transactions from the three months before this period ({0} – {1}) that are not yet marked as VAT filed.",
// 						[user_date(lb_from), user_date(lb_to)]),
// 					previous,
// 					`<div class="vtx-banner">${__("Select only the transactions approved for this return.")}</div>`)}
// 			</div>
// 			<aside class="vtx-aside">
// 				<h5>${__("Return summary")}</h5>
// 				<div class="vtx-muted vtx-sel-text"></div>
// 				<div class="vtx-line"><span>${__("Output VAT (sales)")}</span><b class="vtx-out"></b></div>
// 				<div class="vtx-line"><span>${__("Input VAT (purchases)")}</span><b class="vtx-in"></b></div>
// 				<div class="vtx-net">
// 					<div class="vtx-net-label"></div>
// 					<div class="vtx-net-val"></div>
// 				</div>
// 				<button type="button" class="vtx-btn vtx-continue">${__("Continue to filing")} →</button>
// 				<button type="button" class="vtx-btn vtx-btn-light vtx-close">${__("Close")}</button>
// 			</aside>
// 		</div>
// 	</div>`;
 
// 	const $w = d.fields_dict.body.$wrapper;
// 	$w.html(html);
 
// 	const chosen_rows = () => rows.filter((r) => selected.has(r.key));
// 	let totals = { output: 0, input: 0, net: 0 };
 
// 	// Updates in place (no re-render), so keyboard focus is kept
// 	function refresh() {
// 		$w.find(".vtx-row").each(function () {
// 			$(this).toggleClass("on", selected.has($(this).attr("data-key")));
// 		});
 
// 		[[1, current], [2, previous]].forEach(([n, list]) => {
// 			const eligible = list.filter((r) => !r.locked);
// 			const chosen = eligible.filter((r) => selected.has(r.key)).length;
// 			$w.find(`[data-count-for="${n}"]`).text(__("{0} of {1} selected", [chosen, eligible.length]));
// 		});
 
// 		const chosen = chosen_rows();
// 		const out = chosen.filter((r) => r.type === "Sales").reduce((a, r) => a + r.vat, 0);
// 		const inp = chosen.filter((r) => r.type === "Purchase").reduce((a, r) => a + r.vat, 0);
// 		const net = out - inp;
// 		totals = { output: out, input: inp, net: net };
 
// 		$w.find(".vtx-sel-text").text(
// 			chosen.length === 1 ? __("1 transaction selected") : __("{0} transactions selected", [chosen.length])
// 		);
// 		$w.find(".vtx-out").text(money(out));
// 		$w.find(".vtx-in").text("− " + money(inp));
// 		$w.find(".vtx-net-label").text(net >= 0 ? __("Net VAT payable") : __("Net VAT refundable"));
// 		$w.find(".vtx-net-val").text(money(Math.abs(net)));
// 		$w.find(".vtx-continue").prop("disabled", chosen.length === 0);
// 	}
 
// 	$w.on("change", ".vtx-row input[type=checkbox]", function () {
// 		const key = $(this).closest(".vtx-row").attr("data-key");
// 		this.checked ? selected.add(key) : selected.delete(key);
// 		refresh();
// 	});
 
// 	// Opening a voucher link must not tick the row
// 	$w.on("click", ".vtx-link", (e) => e.stopPropagation());
// 	$w.on("click", ".vtx-close", () => d.hide());
 
// 	$w.on("click", ".vtx-continue", () => {
// 		const chosen = chosen_rows();
// 		const net_text =
// 			totals.net >= 0
// 				? __("VAT Payable {0}", [money(totals.net)])
// 				: __("VAT Receivable {0}", [money(-totals.net)]);
 
// 		frappe.confirm(
// 			__("Create the VAT Journal Entry for {0} transaction(s)?", [chosen.length]) +
// 				"<br><br>" +
// 				__("Output VAT {0}, Input VAT {1} → {2}", [money(totals.output), money(totals.input), net_text]),
// 			() => {
// 				frappe.call({
// 					method: vat_method("create_vat_journal_entry"),
// 					args: {
// 						company: f.company,
// 						from_date: f.from_date,
// 						to_date: f.to_date,
// 						keys: chosen.map((r) => r.key),
// 					},
// 					freeze: true,
// 					freeze_message: __("Creating Journal Entry..."),
// 					callback(r) {
// 						if (!r.message) return;
// 						d.hide();
// 						after_je_created(r.message);
// 						frappe.query_report.refresh();
// 					},
// 				});
// 			}
// 		);
// 	});
 
// 	refresh();
// 	d.show();
// }
 
// // Builds "<app>.<module>.report.<report>.<report>.<function>" from the report record,
// // so you do not have to type the path. If it ever fails, hard-code it here instead.
// function vat_method(fn) {
// 	const rep = frappe.query_report.report_doc;
// 	const app = frappe.boot.module_app[frappe.scrub(rep.module)];
// 	const r = frappe.scrub(rep.name);
// 	return `${app}.${frappe.scrub(rep.module)}.report.${r}.${r}.${fn}`;
// }
 
// function after_je_created(res) {
// 	const money = (v) => format_currency(v, frappe.boot.sysdefaults.currency || "AED");
// 	const net_line =
// 		res.net >= 0
// 			? __("VAT Payable: {0}", [money(res.net)])
// 			: __("VAT Receivable: {0}", [money(-res.net)]);
 
// 	const d = new frappe.ui.Dialog({
// 		title: __("VAT Journal Entry created"),
// 		fields: [
// 			{
// 				fieldtype: "HTML",
// 				options: `<p>${__("Draft entry")} <a href="${frappe.utils.get_form_link("Journal Entry", res.name)}" target="_blank"><b>${res.name}</b></a>
// 				${__("was created. Please review and submit it.")}</p>
// 				<p>${__("Output VAT")}: ${money(res.output)}<br>${__("Input VAT")}: ${money(res.input)}<br><b>${net_line}</b></p>`,
// 			},
// 		],
// 		primary_action_label: __("Record payment / refund"),
// 		primary_action() {
// 			d.hide();
// 			record_vat_settlement(res.name);
// 		},
// 		secondary_action_label: __("Open Journal Entry"),
// 		secondary_action() {
// 			frappe.set_route("Form", "Journal Entry", res.name);
// 		},
// 	});
// 	d.show();
// }
 
// // Second entry: pay the VAT to the FTA (Dr VAT Payable, Cr Bank) or
// // record a refund received (Dr Bank, Cr VAT Receivable).
// function record_vat_settlement(journal_entry) {
// 	const company = frappe.query_report.get_filter_value("company");
// 	const d = new frappe.ui.Dialog({
// 		title: __("VAT payment / refund for {0}", [journal_entry]),
// 		fields: [
// 			{
// 				fieldname: "bank_account",
// 				label: __("Bank Account"),
// 				fieldtype: "Link",
// 				options: "Account",
// 				reqd: 1,
// 				get_query: () => ({
// 					filters: { company: company, account_type: ["in", ["Bank", "Cash"]], is_group: 0 },
// 				}),
// 			},
// 			{ fieldname: "posting_date", label: __("Posting Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
// 			{ fieldname: "reference_no", label: __("Reference No"), fieldtype: "Data", reqd: 1 },
// 			{ fieldname: "reference_date", label: __("Reference Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
// 		],
// 		primary_action_label: __("Create"),
// 		primary_action(v) {
// 			frappe.call({
// 				method: vat_method("create_vat_settlement_entry"),
// 				args: Object.assign({ journal_entry: journal_entry }, v),
// 				freeze: true,
// 				callback(r) {
// 					if (!r.message) return;
// 					d.hide();
// 					frappe.show_alert({ message: __("Draft Bank Entry {0} created", [r.message]), indicator: "green" });
// 					frappe.set_route("Form", "Journal Entry", r.message);
// 				},
// 			});
// 		},
// 	});
// 	d.show();
// }
 
// const VAT_CSS = `
// .vtx{color:#111827}
// .vtx-head{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:16px}
// .vtx-card{background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:10px 14px}
// .vtx-card small{display:block;color:#4B5563;font-size:12px}
// .vtx-card b{font-size:14px}
// .vtx-draft{margin-left:auto;background:#FEF3C7;color:#92400E;font-size:12px;font-weight:600;padding:4px 10px;border-radius:999px}
// .vtx-layout{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}
// .vtx-main{flex:999 1 520px;min-width:0;display:flex;flex-direction:column;gap:20px}
// .vtx-sec{background:#fff;border:1px solid #E5E7EB;border-radius:16px;overflow:hidden}
// .vtx-sec-h{padding:16px 20px;border-bottom:1px solid #EEF0F3;display:flex;flex-wrap:wrap;gap:10px;justify-content:space-between;align-items:center}
// .vtx-sec-h h5{margin:0;font-size:16px;font-weight:600;display:flex;align-items:center;gap:10px}
// .vtx-sec-h p{margin:4px 0 0 36px;font-size:13px;color:#4B5563}
// .vtx-num{width:26px;height:26px;border-radius:8px;background:#CCFBF1;color:#115E59;font-size:13px;font-weight:700;display:inline-flex;align-items:center;justify-content:center}
// .vtx-count{font-size:13px;font-weight:600;color:#115E59;background:#F0FDFA;border:1px solid #99F6E4;padding:5px 12px;border-radius:999px}
// .vtx-banner{margin:12px 12px 0;padding:10px 14px;border-radius:10px;background:#FFFBEB;border:1px solid #FDE68A;color:#78350F;font-size:13px;line-height:1.5}
// .vtx-list{padding:10px;display:flex;flex-direction:column;gap:8px}
// .vtx-row{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;padding:12px 14px;margin:0;border:1px solid #E5E7EB;border-radius:12px;background:#fff;cursor:pointer;font-weight:400}
// .vtx-row.on{background:#F0FDFA;border-color:#5EEAD4}
// .vtx-row.locked{background:#F9FAFB;opacity:.75;cursor:not-allowed}
// .vtx-row input[type=checkbox]{margin:0 !important;flex:none;accent-color:#0F766E}
// .vtx-row-main{flex:1 1 200px;min-width:0}
// .vtx-row-top{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
// .vtx-link{font-weight:600;font-size:14px;color:#111827}
// .vtx-meta{font-size:12px;color:#4B5563;margin-top:3px}
// .vtx-amt{font-size:15px;font-weight:600;white-space:nowrap;font-variant-numeric:tabular-nums}
// .vtx-badge{font-size:12px;font-weight:600;padding:2px 8px;border-radius:6px}
// .vtx-badge-sales{background:#E0F2FE;color:#075985}
// .vtx-badge-purchase{background:#EDE9FE;color:#5B21B6}
// .vtx-note{font-size:12px;font-weight:600;padding:2px 8px;border-radius:6px;background:#F3F4F6;color:#4B5563}
// .vtx-note-locked{background:#FEE4E2;color:#B42318}
// .vtx-empty{padding:16px;color:#6B7280;font-size:13px}
// .vtx-aside{flex:1 1 280px;min-width:0;position:sticky;top:0;background:#fff;border:1px solid #E5E7EB;border-radius:16px;padding:20px;display:flex;flex-direction:column;gap:14px;box-sizing:border-box}
// .vtx-aside h5{margin:0;font-size:16px;font-weight:600}
// .vtx-muted{font-size:13px;color:#4B5563;margin-top:-8px}
// .vtx-line{display:flex;justify-content:space-between;gap:12px;font-size:14px;color:#374151}
// .vtx-line b{color:#111827;font-variant-numeric:tabular-nums}
// .vtx-net{border-top:1px dashed #D1D5DB;padding-top:14px}
// .vtx-net-label{font-size:13px;font-weight:600;color:#4B5563}
// .vtx-net-val{font-size:28px;font-weight:700;color:#0F766E;font-variant-numeric:tabular-nums;line-height:1.2}
// .vtx-btn{width:100%;min-height:44px;border:0;border-radius:12px;background:#0F766E;color:#fff;font-size:14px;font-weight:600;cursor:pointer}
// .vtx-btn:disabled{opacity:.45;cursor:not-allowed}
// .vtx-btn-light{background:#fff;color:#111827;border:1px solid #D1D5DB}
// `;
// // Claude finished the response




frappe.query_reports["UAE VAT 201 Orion"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "drilldown_key",
			fieldtype: "Data",
			hidden: 1,
		},
	],
 
	open_drilldown: function (key) {
		if (!key) return;
		frappe.query_report.set_filter_value({ drilldown_key: key });
		frappe.query_report.page.set_primary_action(__("Back to Summary"), function () {
			frappe.query_report.set_filter_value({ drilldown_key: "" });
			frappe.query_report.page.clear_primary_action();
		});
	},
 
	onload: function (report) {
		if (report.get_filter_value("drilldown_key")) {
			report.page.set_primary_action(__("Back to Summary"), function () {
				frappe.query_report.set_filter_value({ drilldown_key: "" });
				report.page.clear_primary_action();
			});
		}
 
		// NEW: "See Transactions" button
		report.page.add_inner_button(__("Mark As Filed"), function () {
			open_vat_review(report);
		});
	},
 
	formatter: function (value, row, column, data, default_formatter) {
		// In drilldown mode, just render normally
		if (frappe.query_report.get_filter_value("drilldown_key")) {
			return default_formatter(value, row, column, data);
		}
 
		// Make amount/vat_amount clickable links for drill-down
		if (
			data &&
			data.drilldown_key &&
			(column.fieldname === "amount" || column.fieldname === "vat_amount") &&
			data["raw_" + column.fieldname] !== 0 &&
			value &&
			value !== "-"
		) {
			var formatted = default_formatter(value, row, column, data);
			var onclick =
				"frappe.query_reports['UAE VAT 201 Orion'].open_drilldown('" +
				data.drilldown_key +
				"')";
			return (
				'<a onclick="' +
				onclick +
				'" ' +
				'style="text-decoration:underline;cursor:pointer;">' +
				formatted +
				"</a>"
			);
		}
 
		// Bold section headers and totals
		if (
			data &&
			(data.legend == "VAT on Sales and All Other Outputs" ||
				data.legend == "VAT on Expenses and All Other Inputs" ||
				data.legend == "Total VAT on Sales and All Other Outputs" ||
				data.legend == "Total VAT on Expenses and All Other Inputs") &&
			data.legend == value
		) {
			value = $(`<span>${value}</span>`);
			var $value = $(value).css("font-weight", "bold");
			value = $value.wrap("<p></p>").parent().html();
		}
		return value;
	},
};
 
// =====================================================================
// NEW: "See Transactions" review screen (everything below is new)
// =====================================================================
 
function open_vat_review(report) {
	const f = report.get_values();
	if (!f || !f.company || !f.from_date || !f.to_date) {
		frappe.msgprint(__("Please set Company, From Date and To Date first."));
		return;
	}
 
	// Runs the report itself with a special key (see get_vat_transactions in the .py)
	frappe.call({
		method: "frappe.desk.query_report.run",
		args: {
			report_name: "UAE VAT 201 Orion",
			filters: {
				company: f.company,
				from_date: f.from_date,
				to_date: f.to_date,
				drilldown_key: "vat_transactions",
			},
			ignore_prepared_report: true,
		},
		freeze: true,
		freeze_message: __("Loading transactions..."),
		callback(r) {
			if (r.message) show_vat_review(r.message.result || [], f);
		},
	});
}
 
function show_vat_review(rows, f) {
	// Set to true to show section 1 (current-period list) again.
	// While false the current-period transactions are NOT listed, but they are still
	// part of the return (ticked automatically, counted in the summary and the Journal Entry).
	const SHOW_CURRENT_SECTION = false;
	const PREV_NUM = SHOW_CURRENT_SECTION ? 2 : 1;
 
	const esc = frappe.utils.escape_html;
	const cur = frappe.boot.sysdefaults.currency || "AED";
	const money = (v) => format_currency(v, cur);
	const user_date = (d) => frappe.datetime.str_to_user(d);
 
	const current = rows.filter((r) => r.section === "current");
	const previous = rows.filter((r) => r.section === "previous");
	const lb_from = frappe.datetime.add_months(f.from_date, -3);
	const lb_to = frappe.datetime.add_days(f.from_date, -1);
 
	// Current-period items start ticked. Previous-period items must be approved by the user.
	const selected = new Set(current.filter((r) => !r.locked).map((r) => r.key));
 
	const d = new frappe.ui.Dialog({
		title: __("VAT Return Review"),
		size: "extra-large",
		fields: [{ fieldtype: "HTML", fieldname: "body" }],
	});
 
	const row = (r) => {
		const badge = r.type === "Sales" ? "vtx-badge-sales" : "vtx-badge-purchase";
		const note = r.note
			? `<span class="vtx-note ${r.locked ? "vtx-note-locked" : ""}">${esc(r.note)}</span>`
			: "";
		return `
		<label class="vtx-row ${r.locked ? "locked" : ""}" data-key="${esc(r.key)}">
			<input type="checkbox" ${r.locked ? "disabled" : ""} ${selected.has(r.key) ? "checked" : ""}>
			<div class="vtx-row-main">
				<div class="vtx-row-top">
					<a class="vtx-link" href="${esc(frappe.utils.get_form_link(r.doc_type, r.doc_name))}" target="_blank">${esc(r.doc_name)}</a>
					<span class="vtx-badge ${badge}">${esc(__(r.type))}</span>
					<span class="vtx-note">${esc(r.category)}</span>
					${note}
				</div>
				<div class="vtx-meta">${esc(r.doc_type)} · ${user_date(r.posting_date)} · ${esc(r.party)} · ${__("Amount")} ${money(r.amount)}</div>
			</div>
			<div class="vtx-amt">${money(r.vat)}</div>
		</label>`;
	};
 
	const section = (num, title, sub, list, banner) => `
		<section class="vtx-sec">
			<div class="vtx-sec-h">
				<div>
					<h5><span class="vtx-num">${num}</span>${title}</h5>
					<p>${sub}</p>
				</div>
				<span class="vtx-count" data-count-for="${num}"></span>
			</div>
			${banner || ""}
			<div class="vtx-list">
				${list.length ? list.map(row).join("") : `<div class="vtx-empty">${__("No transactions found")}</div>`}
			</div>
		</section>`;
 
	const html = `
	<style>${VAT_CSS}</style>
	<div class="vtx">
		<div class="vtx-head">
			<div class="vtx-card"><small>${__("Company")}</small><b>${esc(f.company)}</b></div>
			<div class="vtx-card"><small>${__("VAT period")}</small>
				<b>${user_date(f.from_date)} – ${user_date(f.to_date)}</b></div>
		</div>
		<div class="vtx-layout">
			<div class="vtx-main">
				${SHOW_CURRENT_SECTION ? section(1, __("Current VAT-period transactions"),
					__("Eligible transactions from the selected filing period."), current) : ""}
				${section(PREV_NUM, __("Previous-period transactions"),
					__("Transactions from the three months before this period ({0} – {1}) that are not yet marked as VAT filed.",
						[user_date(lb_from), user_date(lb_to)]),
					previous,
					`<div class="vtx-banner">${__("Select only the transactions approved for this return.")}</div>`)}
			</div>
			<aside class="vtx-aside">
				<h5>${__("Return summary")}</h5>
				<div class="vtx-muted vtx-sel-text"></div>
				<div class="vtx-line"><span>${__("Output VAT (sales)")}</span><b class="vtx-out"></b></div>
				<div class="vtx-line"><span>${__("Input VAT (purchases)")}</span><b class="vtx-in"></b></div>
				<div class="vtx-net">
					<div class="vtx-net-label"></div>
					<div class="vtx-net-val"></div>
				</div>
				<button type="button" class="vtx-btn vtx-continue">${__("Continue to filing")} →</button>
				<button type="button" class="vtx-btn vtx-btn-light vtx-close">${__("Close")}</button>
			</aside>
		</div>
	</div>`;
 
	const $w = d.fields_dict.body.$wrapper;
	$w.html(html);
 
	const chosen_rows = () => rows.filter((r) => selected.has(r.key));
	let totals = { output: 0, input: 0, net: 0 };
 
	// Updates in place (no re-render), so keyboard focus is kept
	function refresh() {
		$w.find(".vtx-row").each(function () {
			$(this).toggleClass("on", selected.has($(this).attr("data-key")));
		});
 
		[[1, current], [PREV_NUM, previous]].forEach(([n, list]) => {
			const eligible = list.filter((r) => !r.locked);
			const chosen = eligible.filter((r) => selected.has(r.key)).length;
			$w.find(`[data-count-for="${n}"]`).text(__("{0} of {1} selected", [chosen, eligible.length]));
		});
 
		const chosen = chosen_rows();
		const out = chosen.filter((r) => r.type === "Sales").reduce((a, r) => a + r.vat, 0);
		const inp = chosen.filter((r) => r.type === "Purchase").reduce((a, r) => a + r.vat, 0);
		const net = out - inp;
		totals = { output: out, input: inp, net: net };
 
		$w.find(".vtx-sel-text").text(
			chosen.length === 1 ? __("1 transaction selected") : __("{0} transactions selected", [chosen.length])
		);
		$w.find(".vtx-out").text(money(out));
		$w.find(".vtx-in").text("− " + money(inp));
		$w.find(".vtx-net-label").text(net >= 0 ? __("Net VAT payable") : __("Net VAT refundable"));
		$w.find(".vtx-net-val").text(money(Math.abs(net)));
		$w.find(".vtx-continue").prop("disabled", chosen.length === 0);
	}
 
	$w.on("change", ".vtx-row input[type=checkbox]", function () {
		const key = $(this).closest(".vtx-row").attr("data-key");
		this.checked ? selected.add(key) : selected.delete(key);
		refresh();
	});
 
	// Opening a voucher link must not tick the row
	$w.on("click", ".vtx-link", (e) => e.stopPropagation());
	$w.on("click", ".vtx-close", () => d.hide());
 
	$w.on("click", ".vtx-continue", () => {
		const chosen = chosen_rows();
		const net_text =
			totals.net >= 0
				? __("VAT Payable {0}", [money(totals.net)])
				: __("VAT Receivable {0}", [money(-totals.net)]);
 
		frappe.confirm(
			__("Create the VAT Journal Entry for {0} transaction(s)?", [chosen.length]) +
				"<br><br>" +
				__("Output VAT {0}, Input VAT {1} → {2}", [money(totals.output), money(totals.input), net_text]),
			() => {
				frappe.call({
					method: vat_method("create_vat_journal_entry"),
					args: {
						company: f.company,
						from_date: f.from_date,
						to_date: f.to_date,
						keys: chosen.map((r) => r.key),
					},
					freeze: true,
					freeze_message: __("Creating Journal Entry..."),
					callback(r) {
						if (!r.message) return;
						d.hide();
						after_je_created(r.message);
						frappe.query_report.refresh();
					},
				});
			}
		);
	});
 
	refresh();
	d.show();
}
 
// Builds "<app>.<module>.report.<report>.<report>.<function>" from the report record,
// so you do not have to type the path. If it ever fails, hard-code it here instead.
function vat_method(fn) {
	const rep = frappe.query_report.report_doc;
	const app = frappe.boot.module_app[frappe.scrub(rep.module)];
	const r = frappe.scrub(rep.name);
	return `${app}.${frappe.scrub(rep.module)}.report.${r}.${r}.${fn}`;
}
 
function after_je_created(res) {
	const money = (v) => format_currency(v, frappe.boot.sysdefaults.currency || "AED");
	const net_line =
		res.net >= 0
			? __("VAT Payable: {0}", [money(res.net)])
			: __("VAT Receivable: {0}", [money(-res.net)]);
 
	const d = new frappe.ui.Dialog({
		title: __("VAT Journal Entry created"),
		fields: [
			{
				fieldtype: "HTML",
				options: `<p>${__("Draft entry")} <a href="${frappe.utils.get_form_link("Journal Entry", res.name)}" target="_blank"><b>${res.name}</b></a>
				${__("was created. Please review and submit it.")}</p>
				<p>${__("Output VAT")}: ${money(res.output)}<br>${__("Input VAT")}: ${money(res.input)}<br><b>${net_line}</b></p>`,
			},
		],
		// primary_action_label: __("Record payment / refund"),
		// primary_action() {
		// 	d.hide();
		// 	record_vat_settlement(res.name);
		// },
		secondary_action_label: __("Open Journal Entry"),
		secondary_action() {
			frappe.set_route("Form", "Journal Entry", res.name);
		},
	});
	d.show();
}
 
// Second entry: pay the VAT to the FTA (Dr VAT Payable, Cr Bank) or
// record a refund received (Dr Bank, Cr VAT Receivable).
// function record_vat_settlement(journal_entry) {
// 	const company = frappe.query_report.get_filter_value("company");
// 	const d = new frappe.ui.Dialog({
// 		title: __("VAT payment / refund for {0}", [journal_entry]),
// 		fields: [
// 			{
// 				fieldname: "bank_account",
// 				label: __("Bank Account"),
// 				fieldtype: "Link",
// 				options: "Account",
// 				reqd: 1,
// 				get_query: () => ({
// 					filters: { company: company, account_type: ["in", ["Bank", "Cash"]], is_group: 0 },
// 				}),
// 			},
// 			{ fieldname: "posting_date", label: __("Posting Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
// 			{ fieldname: "reference_no", label: __("Reference No"), fieldtype: "Data", reqd: 1 },
// 			{ fieldname: "reference_date", label: __("Reference Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
// 		],
// 		primary_action_label: __("Create"),
// 		primary_action(v) {
// 			frappe.call({
// 				method: vat_method("create_vat_settlement_entry"),
// 				args: Object.assign({ journal_entry: journal_entry }, v),
// 				freeze: true,
// 				callback(r) {
// 					if (!r.message) return;
// 					d.hide();
// 					frappe.show_alert({ message: __("Draft Bank Entry {0} created", [r.message]), indicator: "green" });
// 					frappe.set_route("Form", "Journal Entry", r.message);
// 				},
// 			});
// 		},
// 	});
// 	d.show();
// }
 
const VAT_CSS = `
.vtx{color:#111827}
.vtx-head{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:16px}
.vtx-card{background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:10px 14px}
.vtx-card small{display:block;color:#4B5563;font-size:12px}
.vtx-card b{font-size:14px}
.vtx-draft{margin-left:auto;background:#FEF3C7;color:#92400E;font-size:12px;font-weight:600;padding:4px 10px;border-radius:999px}
.vtx-layout{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}
.vtx-main{flex:999 1 520px;min-width:0;display:flex;flex-direction:column;gap:20px}
.vtx-sec{background:#fff;border:1px solid #E5E7EB;border-radius:16px;overflow:hidden}
.vtx-sec-h{padding:16px 20px;border-bottom:1px solid #EEF0F3;display:flex;flex-wrap:wrap;gap:10px;justify-content:space-between;align-items:center}
.vtx-sec-h h5{margin:0;font-size:16px;font-weight:600;display:flex;align-items:center;gap:10px}
.vtx-sec-h p{margin:4px 0 0 36px;font-size:13px;color:#4B5563}
.vtx-num{width:26px;height:26px;border-radius:8px;background:#CCFBF1;color:#115E59;font-size:13px;font-weight:700;display:inline-flex;align-items:center;justify-content:center}
.vtx-count{font-size:13px;font-weight:600;color:#115E59;background:#F0FDFA;border:1px solid #99F6E4;padding:5px 12px;border-radius:999px}
.vtx-banner{margin:12px 12px 0;padding:10px 14px;border-radius:10px;background:#FFFBEB;border:1px solid #FDE68A;color:#78350F;font-size:13px;line-height:1.5}
.vtx-list{padding:10px;display:flex;flex-direction:column;gap:8px}
.vtx-row{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;padding:12px 14px;margin:0;border:1px solid #E5E7EB;border-radius:12px;background:#fff;cursor:pointer;font-weight:400}
.vtx-row.on{background:#F0FDFA;border-color:#5EEAD4}
.vtx-row.locked{background:#F9FAFB;opacity:.75;cursor:not-allowed}
.vtx-row input[type=checkbox]{margin:0 !important;flex:none;accent-color:#0F766E}
.vtx-row-main{flex:1 1 200px;min-width:0}
.vtx-row-top{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.vtx-link{font-weight:600;font-size:14px;color:#111827}
.vtx-meta{font-size:12px;color:#4B5563;margin-top:3px}
.vtx-amt{font-size:15px;font-weight:600;white-space:nowrap;font-variant-numeric:tabular-nums}
.vtx-badge{font-size:12px;font-weight:600;padding:2px 8px;border-radius:6px}
.vtx-badge-sales{background:#E0F2FE;color:#075985}
.vtx-badge-purchase{background:#EDE9FE;color:#5B21B6}
.vtx-note{font-size:12px;font-weight:600;padding:2px 8px;border-radius:6px;background:#F3F4F6;color:#4B5563}
.vtx-note-locked{background:#FEE4E2;color:#B42318}
.vtx-empty{padding:16px;color:#6B7280;font-size:13px}
.vtx-aside{flex:1 1 280px;min-width:0;position:sticky;top:0;background:#fff;border:1px solid #E5E7EB;border-radius:16px;padding:20px;display:flex;flex-direction:column;gap:14px;box-sizing:border-box}
.vtx-aside h5{margin:0;font-size:16px;font-weight:600}
.vtx-muted{font-size:13px;color:#4B5563;margin-top:-8px}
.vtx-line{display:flex;justify-content:space-between;gap:12px;font-size:14px;color:#374151}
.vtx-line b{color:#111827;font-variant-numeric:tabular-nums}
.vtx-net{border-top:1px dashed #D1D5DB;padding-top:14px}
.vtx-net-label{font-size:13px;font-weight:600;color:#4B5563}
.vtx-net-val{font-size:28px;font-weight:700;color:#0F766E;font-variant-numeric:tabular-nums;line-height:1.2}
.vtx-btn{width:100%;min-height:44px;border:0;border-radius:12px;background:#0F766E;color:#fff;font-size:14px;font-weight:600;cursor:pointer}
.vtx-btn:disabled{opacity:.45;cursor:not-allowed}
.vtx-btn-light{background:#fff;color:#111827;border:1px solid #D1D5DB}
`;
// Claude finished the response
 
 
 
 
