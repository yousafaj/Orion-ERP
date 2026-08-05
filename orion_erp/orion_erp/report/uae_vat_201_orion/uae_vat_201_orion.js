// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

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
