frappe.listview_settings["Leave Application"] = {

    add_fields: [
        "custom_approval_status",
        "custom_medical_certificate_status"
    ],

    has_indicator_for_draft: false,

    formatters: {
        custom_medical_certificate_status(value, df, doc) {
            var color = {
                "Submitted": "green",
                "Pending": "orange",
            }[value] || "blue";
            return `<span class="indicator-pill ${color}">${value}</span>`;
        }
    },

    get_indicator(doc) {

        let status =
            doc.custom_approval_status || "Pending Approval from Approver 1";

        return [
            __(status),
            get_indicator_color(status),
            "custom_approval_status,=," + status
        ];
    }
};


function get_indicator_color(status) {

    if (status === "Approved") {
        return "green";
    }

    if (status === "Rejected") {
        return "red";
    }

    if (status === "Cancelled") {
        return "darkgrey";
    }

    return "blue";
}


// Reorder list view columns to: ID, Employee Name, From Date, Medical Certificate Status, Approval Status, Total Leave
(function () {

    const original_setup_columns =
        frappe.views.ListView.prototype.setup_columns;

    frappe.views.ListView.prototype.setup_columns = function () {

        original_setup_columns.apply(this, arguments);

        if (this.doctype !== "Leave Application") return;

        // Remove native status column
        this.columns = this.columns.filter(function (col) {
            return col.df && col.df.fieldname !== "status";
        });

        // Ensure custom_approval_status column exists
        var hasApprovalStatus = this.columns.some(function (col) {
            return col.df && col.df.fieldname === "custom_approval_status";
        });

        if (!hasApprovalStatus) {
            var df = frappe.meta.get_docfield(
                "Leave Application",
                "custom_approval_status"
            );
            if (df) {
                this.columns.push({
                    type: "Field",
                    df: df
                });
            }
        }

        // Desired column order (Subject/ID is always first at index 0)
        var order = [
            "employee_name",
            "from_date",
            "custom_medical_certificate_status",
            "custom_approval_status",
            "total_leave_days"
        ];

        // Build ordered columns, put any unmatched columns at the end
        var used = {};
        var remaining = [];

        for (var i = 0; i < this.columns.length; i++) {
            var col = this.columns[i];
            var fieldname = col.df ? col.df.fieldname : null;
            if (fieldname && order.indexOf(fieldname) !== -1 && !used[fieldname]) {
                used[fieldname] = col;
            } else {
                remaining.push(col);
            }
        }

        var ordered = [];
        for (var j = 0; j < order.length; j++) {
            if (used[order[j]]) {
                ordered.push(used[order[j]]);
            }
        }

        // Subject column stays first, then ordered fields, then remaining (Tag, Status)
        var subjectCol = remaining.length > 0 ? remaining.shift() : null;
        if (subjectCol && subjectCol.type === "Subject") {
            this.columns = [subjectCol].concat(ordered).concat(remaining);
        } else {
            this.columns = ordered.concat(remaining);
        }
    };

})();