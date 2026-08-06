frappe.query_reports["User Activity Report"] = {
	filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.add_days(frappe.datetime.get_today(), -1), -3),
            on_change: function(report) {
                let from_date = frappe.query_report.get_filter_value("from_date");
                let to_date = frappe.query_report.get_filter_value("to_date");
                let today = frappe.datetime.get_today();

                // Future date check
                if (from_date && frappe.datetime.str_to_obj(from_date) > frappe.datetime.str_to_obj(today)) {
                    frappe.msgprint({
                        title: "Invalid Date",
                        message: "From Date cannot be a future date.",
                        indicator: "red"
                    });
                    report.set_filter_value("from_date", "");
                    return;
                }

                // From Date and To Date check
                if (from_date && to_date && frappe.datetime.str_to_obj(from_date) > frappe.datetime.str_to_obj(to_date) && frappe.datetime.str_to_obj(from_date) <= frappe.datetime.str_to_obj(today)) {
                    frappe.msgprint({
                        title: __("Invalid Date Range"),
                        message: __("From Date cannot be after To Date."),
                        indicator: "red"
                    });
                    report.set_filter_value("from_date", "");
                }
                frappe.call({
                    method: "frappe.client.get",
                    args: {
                        doctype: "Orion Settings",
                        name: "Orion Settings"
                    },
                    callback(r) {
                        const doc = r.message;
                        if (!doc) return;
                        if (doc.enable_tic_report_configuration && doc.allowed_backdated_range_limit_days > 0) {
                            let from_date = frappe.query_report.get_filter_value("from_date");
                            let days = doc.allowed_backdated_range_limit_days;
                            let today = frappe.datetime.get_today();
                            let back_date = frappe.datetime.add_days(today, -days);
                            if (from_date && frappe.datetime.str_to_obj(from_date) < frappe.datetime.str_to_obj(back_date)) {
                                frappe.msgprint({
                                    title: "Data Restricted",
                                    message: `Report shows data for last ${days} days as per Orion Settings - Allowed Backdated Range Limit.`,
                                    indicator: "blue"
                                });
                            }
                        }
                    }
                });
                frappe.query_report.refresh();
            },
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.add_days(frappe.datetime.get_today()),
            on_change: function(report) {
                let from_date = frappe.query_report.get_filter_value("from_date");
                let to_date = frappe.query_report.get_filter_value("to_date");
                let today = frappe.datetime.get_today();

                // From Date and To Date check
                if (from_date && to_date && frappe.datetime.str_to_obj(to_date) < frappe.datetime.str_to_obj(from_date)) {
                    frappe.msgprint({
                        title: __("Invalid Date Range"),
                        message: __("To Date cannot be before From Date."),
                        indicator: "red"
                    });
                    report.set_filter_value("to_date", today);
                }
                frappe.query_report.refresh();
            },
            reqd: 1
        },
        {
            fieldname: "user",
            label: "User",
            fieldtype: "Link",
            options: "User",
            on_change: function(report) {
                frappe.query_report.refresh();
            },
        },
		{
            fieldname: "doctype",
            label: "DocType",
            fieldtype: "Link",
            options: "DocType",
			get_query: function() {
                let module = frappe.query_report.get_filter_value("module");

                let filters = [];

                if (module) {
                    filters.push(["DocType", "module", "=", module]);
                }

                // optional: keep your Setting filter
                filters.push(["DocType", "name", "like", "%Setting%"]);

                return { filters: filters };
			},
			on_change: function(report) {
                // reset field
                report.set_filter_value("fieldname", "");
            },

        },
		{
            fieldname: "module",
            label: "Module",
            fieldtype: "Link",
            options: "Module Def",
            get_query: function() {
                let doctype = frappe.query_report.get_filter_value("doctype");

                if (doctype) {
                    return {
                        query: "orion_erp.orion_erp.report.user_activity_report.user_activity_report.get_module_from_doctype",
                        filters: {
                            doctype: doctype
                        }
                    };
                }
            },
            on_change: function(report) {
                frappe.query_report.refresh();
            }
        },
        {
            fieldname: "change_type",
            label: "Change Type",
            fieldtype: "Select",
            options: "\nUpdate\nInsert\nDelete",
            on_change: function(report) {
                frappe.query_report.refresh();
            },
        },
		{
            fieldname: "fieldname",
            label: "Fieldname",
            fieldtype: "Link",
            options: "DocField",
            get_query: function(report) {
                let doctype = frappe.query_report.get_filter_value("doctype");

                return {
                    query: "orion_erp.orion_erp.report.user_activity_report.user_activity_report.get_docfield_options",
                    filters: {
                        doctype: doctype,
                    }
                };
            },
            on_change: function() {
                let fieldname = frappe.query_report.get_filter_value("fieldname");

                frappe.query_report.set_filter_value("field_label", "");

                // fetch label from DocField
                frappe.call({
                    method: "orion_erp.orion_erp.report.user_activity_report.user_activity_report.get_field_label",
                    args: { fieldname: fieldname },
                    callback: function(r) {
                        if (r.message) {
                            frappe.query_report.set_filter_value("field_label", r.message);
                        }
                    }
                });
            }
        },
        {
            fieldname: "field_label",
            label: "Field Label",
            fieldtype: "Data",
            read_only: 1
        },
    ],
    onload(report) {
        // Show full Report Title
        setTimeout(() => {
            report.page.wrapper.find('.page-title .ellipsis').css({
                'white-space': 'nowrap',
                'overflow': 'visible',
                'text-overflow': 'clip'
            });
        }, 100);
		// Increase Field Label width
		setTimeout(() => {
            let field = report.get_filter("field_label");

            if (field && field.$wrapper) {
                field.$wrapper.css({
                    "min-width": "33.3%",
                    "flex": "0 0 33.3%"
                });
            }

            if (field && field.$input) {
                field.$input.css("width", "100%");
            }
        }, 300);
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Orion Settings",
                name: "Orion Settings"
            },
            callback(r) {
                const doc = r.message;
                if (!doc) return;
                if (doc.enable_tic_report_configuration && doc.allowed_backdated_range_limit_days) {
                    let days = doc.allowed_backdated_range_limit_days;
                    let today = frappe.datetime.get_today();
                    let from_date = frappe.datetime.add_days(today, -days);
                    report.set_filter_value("from_date", from_date);
                }
            }
        });
    },
};
