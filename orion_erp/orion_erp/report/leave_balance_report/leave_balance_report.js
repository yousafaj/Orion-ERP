frappe.query_reports["Leave Balance Report"] = {
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
			fieldname: "employee_category",
			label: __("Employee Category"),
			fieldtype: "Select",
			options: "\nOffice\nNon-Office"
		}
	]
};
