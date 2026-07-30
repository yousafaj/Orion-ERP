(function () {
    var MAX_RETRIES = 20;
    var attempts = 0;

    function apply_patch() {
        if (typeof get_fields_for_doctype !== "function") {
            if (++attempts < MAX_RETRIES) {
                setTimeout(apply_patch, 200);
            }
            return;
        }

        var __orig = get_fields_for_doctype;
        get_fields_for_doctype = function (doctype) {
            return __orig(doctype).then(function (result) {
                var existing = result.map(function (f) { return f.fieldname; });
                var all = frappe.meta.get_docfields(doctype);
                all.forEach(function (df) {
                    if (
                        (df.fieldtype === "Table MultiSelect" || df.fieldtype === "Table Multiselect") &&
                        existing.indexOf(df.fieldname) === -1
                    ) {
                        result.push(df);
                    }
                });
                return result;
            });
        };
    }

    apply_patch();
})();
