frappe.ui.form.ControlTableMultiSelectWebForm = class ControlTableMultiSelectWebForm
    extends frappe.ui.form.ControlTableMultiSelect {

    get_model_value() {
        if (this.rows && this.rows.length) return this.rows.slice();
        var doc_value = this.doc ? this.doc[this.df.fieldname] : null;
        if (doc_value && doc_value.length) {
            this.rows = doc_value;
            return this.rows.slice();
        }
        return [];
    }

    get_link_field() {
        if (this._link_field) return this._link_field;
        this._link_field = (this.df.fields || []).find(function(df) {
            return df.fieldtype === "Link";
        });
        if (!this._link_field) {
            var meta = frappe.get_meta(this.df.options);
            if (meta && meta.fields) {
                this._link_field = meta.fields.find(function(df) {
                    return df.fieldtype === "Link";
                });
            }
        }
        if (!this._link_field) {
            console.warn("Table MultiSelect: no Link field found in", this.df.options);
        }
        return this._link_field;
    }

    make_input() {
        super.make_input();
        var me = this;
        this.$input_area.off("click", ".btn-remove");
        this.$input_area.on("click", ".btn-remove", function () {
            var $value = $(this).closest(".tb-selected-value");
            var value = decodeURIComponent($value.data().value);
            var link_field = me.get_link_field();
            me.rows = me.rows.filter(function (row) {
                return row[link_field.fieldname] !== value;
            });
            me._sync_doc();
            me.parse_validate_and_set_in_model("");
        });
    }

    parse(value, label) {
        if (typeof value == "object" || !this.rows) return value;
        var link_field = this.get_link_field();
        if (value) {
            this.rows.push({ [link_field.fieldname]: value });
            frappe.utils.add_link_title(link_field.options, value, label);
        }
        this._rows_list = this.rows.map(function (row) {
            return row[link_field.fieldname];
        });
        this._sync_doc();
        return this.rows;
    }

    validate(value) {
        var rows = (value || []).slice();
        if (this.df.ignore_link_validation || rows.length === 0) return rows;
        var link_field = this.get_link_field();
        var all_rows_except_last = rows.slice(0, rows.length - 1);
        var last_row = rows[rows.length - 1];
        var link_value = last_row ? last_row[link_field.fieldname] : null;
        if (!link_value) return all_rows_except_last;
        if (all_rows_except_last.map(function (r) { return r[link_field.fieldname]; }).includes(link_value)) {
            return all_rows_except_last;
        }
        var me = this;
        return frappe.xcall("frappe.client.validate_link", {
            doctype: link_field.options,
            docname: link_value,
        }).then(function (response) {
            return response && response.name === link_value ? rows : all_rows_except_last;
        });
    }

    set_disp_area(value) {
        if (!this.disp_area) return;
        if (!value || !value.length) {
            this.$disp_area && this.$disp_area.html("");
            return;
        }
        var link_field = this.get_link_field();
        if (!link_field) return;
        var display_values = value.map(function (row) {
            return row[link_field.fieldname] || "";
        });
        this.$disp_area && this.$disp_area.html(display_values.join(", "));
    }

    set_formatted_input(value) {
        this.rows = value || [];
        this._sync_doc();
        var link_field = this.get_link_field();
        if (!link_field) return;
        var values = this.rows.map(function (row) {
            return row[link_field.fieldname];
        });
        this.set_pill_html(values);
    }

    _sync_doc() {
        if (this.doc) {
            this.doc[this.df.fieldname] = this.rows;
        }
    }
};
