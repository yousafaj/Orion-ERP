frappe.listview_settings["Leave Application"] = {

    add_fields: [
        "custom_approval_status"
    ],

    has_indicator_for_draft: false,

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


// Ensure custom_approval_status replaces status in list view columns
(function () {

    const original_setup_columns =
        frappe.views.ListView.prototype.setup_columns;

    frappe.views.ListView.prototype.setup_columns = function () {

        original_setup_columns.apply(this, arguments);

        if (this.doctype !== "Leave Application") return;

        // Remove the native status column
        this.columns = this.columns.filter(function (col) {
            return col.df && col.df.fieldname !== "status";
        });

        // Add custom_approval_status column if not already present
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
    };

})();