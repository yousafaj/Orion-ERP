// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

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

	open_drilldown: function (data, drilldown_type) {
		if (!data) return;
		frappe.query_report.set_filter_value({
			drilldown_type: drilldown_type,
			drilldown_vehicle: data.vehicle || "",
			drilldown_company: data.company || frappe.query_report.get_filter_value("company") || ""
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

		if (amount_fields.indexOf(column.fieldname) !== -1 && value && data) {
			var formatted = default_formatter(value, row, column, data);
			var onclick_data = JSON.stringify(data).replace(/"/g, "&quot;");
			var onclick = "frappe.query_reports['Vehicle-wise Gross Profit Report'].open_drilldown(" +
				onclick_data + ", '" + column.fieldname + "')";
			return (
				'<a onclick="' + onclick + '" ' +
				'style="text-decoration:underline;cursor:pointer;">' +
				formatted +
				"</a>"
			);
		}

		return default_formatter(value, row, column, data);
	}
};
