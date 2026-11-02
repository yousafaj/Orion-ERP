// // Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// // For license information, please see license.txt

// frappe.query_reports["Vehicle-wise Gross Profit Report"] = {
// 	filters: [
// 		{
// 			fieldname: "from_date",
// 			label: __("From Date"),
// 			fieldtype: "Date",
// 			reqd: 1
// 		},
// 		{
// 			fieldname: "to_date",
// 			label: __("To Date"),
// 			fieldtype: "Date",
// 			reqd: 1
// 		},
// 		{
// 			fieldname: "company",
// 			label: __("Company"),
// 			fieldtype: "Link",
// 			options: "Company"
// 		},
// 		{
// 			fieldname: "cost_center",
// 			label: __("Cost Center"),
// 			fieldtype: "Link",
// 			options: "Cost Center"
// 		},
// 		{
// 			fieldname: "vehicle",
// 			label: __("Vehicle"),
// 			fieldtype: "Link",
// 			options: "Vehicle"
// 		},
// 		{
// 			fieldname: "consolidated",
// 			label: __("Consolidated"),
// 			fieldtype: "Check",
// 			default: 0
// 		},
// 		{
// 			fieldname: "drilldown_type",
// 			fieldtype: "Data",
// 			hidden: 1
// 		},
// 		{
// 			fieldname: "drilldown_vehicle",
// 			fieldtype: "Data",
// 			hidden: 1
// 		},
// 		{
// 			fieldname: "drilldown_company",
// 			fieldtype: "Data",
// 			hidden: 1
// 		}
// 	],

// 	open_drilldown: function (data, drilldown_type) {
// 		if (!data) return;
// 		frappe.query_report.set_filter_value({
// 			drilldown_type: drilldown_type,
// 			drilldown_vehicle: data.vehicle || "",
// 			drilldown_company: data.company || frappe.query_report.get_filter_value("company") || ""
// 		});
// 		frappe.query_report.page.set_primary_action(__("Back to Summary"), function () {
// 			frappe.query_report.set_filter_value({
// 				drilldown_type: "",
// 				drilldown_vehicle: "",
// 				drilldown_company: ""
// 			});
// 			frappe.query_report.page.clear_primary_action();
// 		});
// 	},

// 	onload: function (report) {
// 		if (report.get_filter_value("drilldown_type")) {
// 			report.page.set_primary_action(__("Back to Summary"), function () {
// 				frappe.query_report.set_filter_value({
// 					drilldown_type: "",
// 					drilldown_vehicle: "",
// 					drilldown_company: ""
// 				});
// 				report.page.clear_primary_action();
// 			});
// 		}
// 	},

// 	formatter: function (value, row, column, data, default_formatter) {
// 		var amount_fields = [
// 			"sales_amount", "purchase_amount",
// 			"jv_debit_amount", "jv_credit_amount",
// 			"gross_profit"
// 		];

// 		if (frappe.query_report.get_filter_value("drilldown_type")) {
// 			return default_formatter(value, row, column, data);
// 		}

// 		if (amount_fields.indexOf(column.fieldname) !== -1 && value && data) {
// 			var formatted = default_formatter(value, row, column, data);
// 			var onclick_data = JSON.stringify(data).replace(/"/g, "&quot;");
// 			var onclick = "frappe.query_reports['Vehicle-wise Gross Profit Report'].open_drilldown(" +
// 				onclick_data + ", '" + column.fieldname + "')";
// 			return (
// 				'<a onclick="' + onclick + '" ' +
// 				'style="text-decoration:underline;cursor:pointer;">' +
// 				formatted +
// 				"</a>"
// 			);
// 		}

// 		return default_formatter(value, row, column, data);
// 	}
// };



const STATEMENT_METHOD =
	"orion_erp.orion_erp.report.vehicle_wise_gross_profit_report.vehicle_wise_gross_profit_report.get_vehicle_statement";
const EXPORT_METHOD =
	"orion_erp.orion_erp.report.vehicle_wise_gross_profit_report.vehicle_wise_gross_profit_report.export_vehicle_statement";
 
// Totals per company for the popup (used when the vehicle has entries in more than one company)
function vgp_summarise_by_company(d) {
	const by = {};
	const add = (rows, key) =>
		(rows || []).forEach((x) => {
			const c = x.company || "";
			by[c] = by[c] || { sales: 0, purchase: 0, jv_debit: 0, jv_credit: 0 };
			by[c][key] += flt(x.amount);
		});
	add(d.sales, "sales");
	add(d.purchases, "purchase");
	add(d.jv_debits, "jv_debit");
	add(d.jv_credits, "jv_credit");
	Object.keys(by).forEach((c) => {
		by[c].gross_profit = by[c].sales - by[c].purchase - by[c].jv_debit + by[c].jv_credit;
	});
	return by;
}
 
frappe.query_reports["Vehicle-wise Gross Profit Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company"
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center"
		},
		{
			fieldname: "vehicle",
			label: __("Vehicle"),
			fieldtype: "Link",
			options: "Vehicle"
		},
		{
			fieldname: "consolidated",
			label: __("Consolidated"),
			fieldtype: "Check",
			default: 0
		},
		{
			fieldname: "drilldown_type",
			fieldtype: "Data",
			hidden: 1
		},
		{
			fieldname: "drilldown_vehicle",
			fieldtype: "Data",
			hidden: 1
		},
		{
			fieldname: "drilldown_company",
			fieldtype: "Data",
			hidden: 1
		}
	],
 
	// Full-page drill-down (Sales / Purchase / JV Debit / JV Credit / Gross Profit columns)
	open_drilldown: function (data, drilldown_type) {
		if (!data) return;
		frappe.query_report.set_filter_value({
			drilldown_type: drilldown_type,
			drilldown_vehicle: data.vehicle || "",
			// drilldown_company: data.company || frappe.query_report.get_filter_value("company") || ""

			drilldown_company: cint(frappe.query_report.get_filter_value("consolidated"))
			? ""
			: (data.company || frappe.query_report.get_filter_value("company") || "")
		});
		frappe.query_report.page.set_primary_action(__("Back to Summary"), function () {
			frappe.query_report.set_filter_value({
				drilldown_type: "",
				drilldown_vehicle: "",
				drilldown_company: ""
			});
			frappe.query_report.page.clear_primary_action();
		});
	},
 
	// Popup statement - opened by clicking the VEHICLE NO.
	// Shows the vehicle's sales, purchases and JV debits/credits for ALL companies
	// (leave the Company filter in the popup empty). Company, dates and cost center
	// can be changed inside the popup.
	open_statement: function (vehicle) {
		const rf = frappe.query_report.get_filter_values();
		const fmt = (v) => format_currency(v || 0);
		const esc = (v) => frappe.utils.escape_html(v == null ? "" : String(v));
 
		let seq = 0; // ignores answers of older requests
		let timer = null;
		let ready = false;
 
		const dialog = new frappe.ui.Dialog({
			title: __("Vehicle Wise Consolidated Profit Report"),
			size: "extra-large",
			fields: [
				{
					fieldname: "company",
					label: __("Company"),
					fieldtype: "Link",
					options: "Company",
					// Consolidated report = all companies. Otherwise start with the report's company.
					default: cint(rf.consolidated) ? "" : rf.company || "",
					description: __("Leave empty to show all companies"),
					change: () => schedule()
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "cost_center",
					label: __("Cost Center"),
					fieldtype: "Link",
					options: "Cost Center",
					default: rf.cost_center || "",
					get_query: () => {
						const c = dialog.get_value("company");
						return c ? { filters: { company: c } } : {};
					},
					change: () => schedule()
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "from_date",
					label: __("From Date"),
					fieldtype: "Date",
					reqd: 1,
					default: rf.from_date,
					change: () => schedule()
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "to_date",
					label: __("To Date"),
					fieldtype: "Date",
					reqd: 1,
					default: rf.to_date,
					change: () => schedule()
				},
				{ fieldtype: "Section Break" },
				{ fieldtype: "HTML", fieldname: "statement" }
			]
		});
 
		const $out = dialog.fields_dict.statement.$wrapper;
 
		// Export button: downloads everything shown here (current popup filters) as an Excel file
		dialog.set_primary_action(__("Export"), function () {
			const v = dialog.get_values(true) || {};
			if (!v.from_date || !v.to_date) {
				frappe.msgprint(__("Please set From Date and To Date."));
				return;
			}
			open_url_post(frappe.request.url, {
				cmd: EXPORT_METHOD,
				vehicle: vehicle,
				from_date: v.from_date,
				to_date: v.to_date,
				company: v.company || "",
				cost_center: v.cost_center || ""
			});
		});
 
		function schedule() {
			if (!ready) return;
			clearTimeout(timer);
			timer = setTimeout(load, 400);
		}
 
		function render(d) {
			const section = (title, rows, total_label, total) => {
				let html = `<tr><td colspan="5" style="background:#f3f3f3;font-weight:bold;">${title}</td></tr>`;
				if (!rows.length) {
					html += `<tr><td colspan="5" class="text-muted">${__("No transactions")}</td></tr>`;
				}
				rows.forEach((x) => {
					html += `<tr>
						<td>${esc(x.company)}</td>
						<td>${esc(x.ref)}</td>
						<td>${x.date ? frappe.datetime.str_to_user(x.date) : ""}</td>
						<td>${esc(x.party)}${x.details ? " – " + esc(x.details) : ""}</td>
						<td class="text-right">${fmt(x.amount)}</td>
					</tr>`;
				});
				html += `<tr style="font-weight:bold;">
					<td colspan="4" class="text-right">${total_label}</td>
					<td class="text-right">${fmt(total)}</td></tr>`;
				return html;
			};
 
			let html = `
				<div style="margin-bottom:8px;font-size:14px;">${__("Vehicle No")}: <b>${esc(vehicle)}</b></div>
				<table class="table table-bordered table-sm">
					<thead><tr>
						<th>${__("Company")}</th>
						<th>${__("Reference")}</th>
						<th>${__("Date")}</th>
						<th>${__("Details")}</th>
						<th class="text-right">${__("Amount")}</th>
					</tr></thead>
					<tbody>
						${section(__("Sales"), d.sales, __("Total Sales"), d.total_sales)}
						${section(__("Purchase"), d.purchases, __("Total Purchase"), d.total_purchase)}
						${section(__("JV Debits"), d.jv_debits, __("Total JV Debits"), d.total_jv_debit)}
						${section(__("JV Credits"), d.jv_credits, __("Total JV Credits"), d.total_jv_credit)}
						<tr style="font-weight:bold;background:#e8f5e9;">
							<td colspan="4" class="text-right">${__("Gross Profit")}</td>
							<td class="text-right">${fmt(d.gross_profit)}</td>
						</tr>
					</tbody>
				</table>`;
 
			// Company-wise totals, only useful when more than one company has entries
			const by = vgp_summarise_by_company(d);
			const companies = Object.keys(by).sort();
			if (companies.length > 1) {
				html += `
				<h6 style="margin-top:15px;">${__("Company-wise summary")}</h6>
				<table class="table table-bordered table-sm">
					<thead><tr>
						<th>${__("Company")}</th>
						<th class="text-right">${__("Sales")}</th>
						<th class="text-right">${__("Purchase")}</th>
						<th class="text-right">${__("JV Debit")}</th>
						<th class="text-right">${__("JV Credit")}</th>
						<th class="text-right">${__("Gross Profit")}</th>
					</tr></thead>
					<tbody>
						${companies
							.map(
								(c) => `<tr>
							<td>${esc(c)}</td>
							<td class="text-right">${fmt(by[c].sales)}</td>
							<td class="text-right">${fmt(by[c].purchase)}</td>
							<td class="text-right">${fmt(by[c].jv_debit)}</td>
							<td class="text-right">${fmt(by[c].jv_credit)}</td>
							<td class="text-right">${fmt(by[c].gross_profit)}</td>
						</tr>`
							)
							.join("")}
					</tbody>
				</table>`;
			}
			$out.html(html);
		}
 
		function load() {
			const v = dialog.get_values(true) || {};
			if (!v.from_date || !v.to_date) {
				$out.html(`<div class="text-muted" style="padding:15px;">${__("Please set From Date and To Date.")}</div>`);
				return;
			}
			const my = ++seq;
			$out.html(`<div class="text-muted" style="padding:15px;">${__("Loading...")}</div>`);
			frappe.call({
				method: STATEMENT_METHOD,
				args: {
					vehicle: vehicle,
					from_date: v.from_date,
					to_date: v.to_date,
					company: v.company || "",
					cost_center: v.cost_center || ""
				},
				callback: function (r) {
					if (my !== seq || !r.message) return;
					render(r.message);
				},
				error: function () {
					if (my !== seq) return;
					$out.html(`<div class="text-danger" style="padding:15px;">${__("Could not load the transactions.")}</div>`);
				}
			});
		}
 
		dialog.show();
		ready = true;
		load();
	},
 
	onload: function (report) {
		if (report.get_filter_value("drilldown_type")) {
			report.page.set_primary_action(__("Back to Summary"), function () {
				frappe.query_report.set_filter_value({
					drilldown_type: "",
					drilldown_vehicle: "",
					drilldown_company: ""
				});
				report.page.clear_primary_action();
			});
		}
	},
 
	formatter: function (value, row, column, data, default_formatter) {
		var amount_fields = [
			"sales_amount", "purchase_amount",
			"jv_debit_amount", "jv_credit_amount",
			"gross_profit"
		];
 
		if (frappe.query_report.get_filter_value("drilldown_type")) {
			return default_formatter(value, row, column, data);
		}
 
		var rpt = "frappe.query_reports['Vehicle-wise Gross Profit Report']";
 
		// Vehicle No -> popup statement (all companies)
		if (column.fieldname === "vehicle" && data && data.vehicle) {
			var onclick_vehicle = rpt + ".open_statement(" +
				JSON.stringify(data.vehicle).replace(/"/g, "&quot;") + ")";
			return (
				'<a onclick="' + onclick_vehicle + '" ' +
				'style="text-decoration:underline;cursor:pointer;">' +
				frappe.utils.escape_html(data.vehicle) +
				"</a>"
			);
		}
 
		if (amount_fields.indexOf(column.fieldname) !== -1 && data) {
			// Gross Profit: clickable even when 0
			// All other columns: clickable only when value is non-zero
			var clickable = column.fieldname === "gross_profit"
				? (value !== null && value !== undefined && data.vehicle)
				: !!value;
 
			if (clickable) {
				var formatted = default_formatter(value, row, column, data);
				var onclick_data = JSON.stringify(data).replace(/"/g, "&quot;");
				var onclick = rpt + ".open_drilldown(" + onclick_data + ", '" + column.fieldname + "')";
 
				return (
					'<a onclick="' + onclick + '" ' +
					'style="text-decoration:underline;cursor:pointer;">' +
					formatted +
					"</a>"
				);
			}
		}
 
		return default_formatter(value, row, column, data);
	}
};
