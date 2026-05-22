// Copyright (c) 2026, osama.ahmed@deliverydevs.com
// For license information, please see license.txt

frappe.query_reports["Upcoming Leave Report"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			on_change: function(report) {
				validate_dates(report);
			}
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			on_change: function(report) {
				validate_dates(report);
			}
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			get_query: function() {
				return {
					filters: {
						status: "Active"
					}
				};
			}
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department"
		},
		{
			fieldname: "leave_type",
			label: __("Leave Type"),
			fieldtype: "Link",
			options: "Leave Type"
		},
		{
			fieldname: "employee_category",
			label: __("Employee Category"),
			fieldtype: "Select",
			options: "\nOffice\nNon-Office"
		}
	]
};

function validate_dates(report) {

	let today = frappe.datetime.get_today();
	let from_date = report.get_filter_value("from_date");
	let to_date = report.get_filter_value("to_date");

	if (from_date && from_date < today) {
		frappe.throw(__("From Date cannot be in the past"));
	}

	if (to_date && to_date < today) {
		frappe.throw(__("To Date cannot be in the past"));
	}

	if (from_date && to_date && from_date > to_date) {
		frappe.throw(__("From Date cannot be greater than To Date"));
	}
}