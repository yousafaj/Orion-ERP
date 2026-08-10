(function () {
    if (!frappe.boot) frappe.boot = {};
    if (!frappe.boot.user) frappe.boot.user = { can_create: [], can_read: [], can_select: [] };

    var style = document.createElement("style");
    style.textContent = ".web-form-wrapper .table-multiselect{display:flex;flex-wrap:wrap;height:auto;padding:10px;padding-bottom:5px;gap:6px}";
    document.head.appendChild(style);

    var __orig = frappe.ui.form.make_control;
    frappe.ui.form.make_control = function (opts) {
        if (opts.df.fieldtype === "Table MultiSelect" && frappe.web_form) {
            return new frappe.ui.form.ControlTableMultiSelectWebForm(opts);
        }
        return __orig(opts);
    };
})();
