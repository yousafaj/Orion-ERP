
// Save original methods
const original_setup_columns = frappe.views.ListView.prototype.setup_columns;
const original_get_meta_html = frappe.views.ListView.prototype.get_meta_html;
const original_get_header_html = frappe.views.ListView.prototype.get_header_html;


/*
   COLUMN ORDER (KEEP CHECKBOX)
*/

frappe.views.ListView.prototype.setup_columns = function () {

    if (this.doctype !== "Employee") {
        return original_setup_columns.apply(this, arguments);
    }

    // Load original columns
    original_setup_columns.apply(this, arguments);

    const get_df = frappe.meta.get_docfield.bind(null, this.doctype);

    // Remove columns if they already exist
    this.columns = this.columns.filter(col => {

        const fieldname = col.df?.fieldname;
        const label = col.df?.label;

        if (fieldname === "name") return false;
        if (fieldname === "employee_name") return false;
        if (fieldname === "designation") return false;

        // Remove Tag column
        if (fieldname === "_user_tags") return false;
        if (label === "Tag") return false;
        if (col.type === "Tag") return false;

        return true;
    });
    const custom_columns = [
        {
            type: "Subject",
            df: {
                label: __("ID"),
                fieldname: "name"
            }
        },
        {
            type: "Field",
            df: get_df("employee_name")
        },
        {
            type: "Field",
            df: get_df("designation")
        }
    ];

    // Insert after checkbox column
    this.columns.splice(0, 0, ...custom_columns);
};


/*
   REMOVE LIKE ICON + COMMENT ICON
*/

frappe.views.ListView.prototype.get_meta_html = function (doc) {

    if (this.doctype !== "Employee") {
        return original_get_meta_html.apply(this, arguments);
    }

    const modified = comment_when(doc.modified, true);

    return `
        <div class="level-item list-row-activity hidden-xs">
            <span class="modified">${modified}</span>
        </div>
        <div class="level-item visible-xs text-right">
            ${this.get_indicator_html(doc)}
        </div>
    `;
};



/* 
   REMOVE "LIKED BY ME" HEADER
*/

frappe.views.ListView.prototype.get_header_html = function () {

    if (this.doctype !== "Employee") {
        return original_get_header_html.apply(this, arguments);
    }

    const subject_field = this.columns[0].df;

    let subject_html = `
        <input class="level-item list-check-all" type="checkbox"
            title="${__("Select All")}">
        <span class="level-item"
            data-sort-by="${subject_field.fieldname}"
            title="${__("Click to sort by {0}", [subject_field.label])}">
            ${__(subject_field.label)}
        </span>
    `;

    const columns_html = this.columns.map(col => {

        let classes = [
            "list-row-col",
            "ellipsis",
            col.type === "Subject" ? "list-subject level" : "hidden-xs"
        ].join(" ");

        let html = "";

        if (col.type === "Subject") {
            html = subject_html;
        } else {
            const label = __(col.df?.label || col.type);
            html = `<span>${label}</span>`;
        }

        return `<div class="${classes}">${html}</div>`;

    }).join("");

    const right_html = `
        <span class="list-count"></span>
    `;

    return this.get_header_html_skeleton(columns_html, right_html);
};

