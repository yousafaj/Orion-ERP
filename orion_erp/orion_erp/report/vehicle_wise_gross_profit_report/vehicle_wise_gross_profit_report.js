// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle-wise Gross Profit Report"] = {
	filters: [
        {
            fieldname: "vehicle",
            label: "Vehicle",
            fieldtype: "Link",
            options: "Vehicle"
        }
    ]
};
