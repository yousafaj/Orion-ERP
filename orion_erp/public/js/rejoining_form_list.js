frappe.listview_settings["Rejoining Form"] = {
    add_fields: [
        "custom_rejoining_approval_status"
    ],

    has_indicator_for_draft: false,

    formatters: {
        custom_rejoining_approval_status(value) {
            if (!value) {
                value = "Open";
            }
            let color = get_indicator_color(value);
            return `<span class="indicator-pill ${color}">${value}</span>`;
        }
    },

    get_indicator(doc) {
        let status = doc.custom_rejoining_approval_status || "Open";
        return [
            __(status),
            get_indicator_color(status),
            "custom_rejoining_approval_status,=," + status
        ];
    }
};

function get_indicator_color(status) {
    if (status === "Approved") {
        return "green";
    }
    if (status === "Rejected" || status === "Cancelled") {
        return "red";
    }
    if (status === "Open" || status === "Submit Pending" || status.startsWith("Pending Approval")) {
        return "orange";
    }
    return "blue";
}

(function () {
    const original_setup_columns = frappe.views.ListView.prototype.setup_columns;

    frappe.views.ListView.prototype.setup_columns = function () {
        original_setup_columns.apply(this, arguments);

        if (this.doctype !== "Rejoining Form") {
            return;
        }

        const hasApprovalStatus = this.columns.some(function (col) {
            return col.df && col.df.fieldname === "custom_rejoining_approval_status";
        });

        if (!hasApprovalStatus) {
            const df = frappe.meta.get_docfield("Rejoining Form", "custom_rejoining_approval_status");
            if (df) {
                this.columns.push({
                    type: "Field",
                    df: df
                });
            }
        }

        const order = [
            "employee_name",
            "custom_rejoining_approval_status"
        ];

        const used = {};
        const remaining = [];

        this.columns.forEach(function (col) {
            const fieldname = col.df ? col.df.fieldname : null;
            if (fieldname && order.includes(fieldname) && !used[fieldname]) {
                used[fieldname] = col;
            } else {
                remaining.push(col);
            }
        });

        const ordered = [];
        order.forEach(function (fieldname) {
            if (used[fieldname]) {
                ordered.push(used[fieldname]);
            }
        });

        const subjectCol = remaining.length > 0 ? remaining.shift() : null;

        if (subjectCol && subjectCol.type === "Subject") {
            this.columns = [subjectCol, ...ordered, ...remaining];
        } else {
            this.columns = [...ordered, ...remaining];
        }
    };
})();
