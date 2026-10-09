// A stale annual preview must not warn after the user switches to Sick Leave.
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");
const source = fs.readFileSync("orion_erp/public/js/leave_application.js", "utf8");
const pending = [];
const properties = [];
let nativeCalls = 0;
const context = {
    frappe: { call: options => pending.push(options) },
    __: text => text,
    native_leave_balance_handlers: [() => { nativeCalls++; }],
    flt: value => Number(value || 0),
};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf("function refresh_projected_leave_balance(frm)"),
    source.indexOf("function add_medical_certificate_selection(frm)")), context);
const frm = {
    doc: { employee: "EMP", leave_type: "ANNUAL", from_date: "2026-11-12", to_date: "2026-11-30" },
    is_new: () => true,
    toggle_display: () => {},
    set_df_property: (...args) => properties.push(args),
    refresh_fields: () => {},
};
context.refresh_projected_leave_balance(frm);
assert.equal(pending[0].args.display_only, 1);
frm.doc.leave_type = "SICK";
pending[0].callback({ message: { projection_error: "Annual dates invalid" } });
assert.equal(properties.length, 0);
context.refresh_projected_leave_balance(frm);
pending[1].callback({ message: null });
Promise.resolve().then(() => {
    assert.equal(nativeCalls, 1);
    assert.equal(properties.find(row => row[1] === "description")[2], "");
    console.log("Passed: stale annual warning discarded; Sick Leave uses native balance.");
});
