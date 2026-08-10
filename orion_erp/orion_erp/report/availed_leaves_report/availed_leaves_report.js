frappe.query_reports["Availed Leaves Report"] = {
	"filters": [
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
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date"
		}
	]
};
