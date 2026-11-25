frappe.ui.form.on("Leave Application", {
    // refresh: load_accrual,
    refresh(frm) {
        add_recall_button(frm);
        load_accrual(frm);
    },

    employee: load_accrual,
    from_date: load_accrual,
    onload_post_render: load_accrual,
});



function add_recall_button(frm) {
    if (frm.doc.docstatus !== 1) return;
    if (!frappe.user.has_role(["HR Manager", "HR User"])) return;

    frm.add_custom_button(__("Recall From Leave"), () => {
        frappe.prompt([
            { fieldname: "rejoin_date", fieldtype: "Date", label: "Rejoining Date",
              reqd: 1, description: "First day back at work" },
            { fieldname: "monthly_salary", fieldtype: "Currency", label: "Monthly Salary",
              description: "Leave empty to use the Vacation Settlement salary" },
        ], v => frappe.call({
            method: "orion_erp.orion_erp.validations.leave_application.advance_paid.recall_leave",
            args: { docname: frm.doc.name, rejoin_date: v.rejoin_date, monthly_salary: v.monthly_salary },
            callback(r) {
                if (r.exc) return;
                frappe.show_alert({ message: __("{0} days returned to balance", [r.message.returned]),
                                    indicator: "green" });
                frm.reload_doc();
            },
        }), __("Recall From Leave"), __("Recall"));
    });
}



function form_root(frm) {
    return $(frm.wrapper || frm.page.wrapper);
}

function find_table(frm) {
    return form_root(frm).find("table").filter(function () {
        return $(this).text().indexOf("Total Allocated Leaves") !== -1;
    }).first();
}

function load_accrual(frm) {
    if (!frm.doc.employee) return;
    frappe.call({
        method: "orion_erp.orion_erp.validations.leave_application.accrual_summary.get_accrual_for_employee",
        args: { employee: frm.doc.employee, from_date: frm.doc.from_date },
        callback(r) {
            frm.__orion_accrual = r.message || {};
            start_watching(frm);
            apply(frm);
        },
    });
}

function apply(frm) {
    const data = frm.__orion_accrual || {};
    const table = find_table(frm);
    if (!table.length || !Object.keys(data).length) return;

    const idx = {};
    table.find("thead tr").first().children().each(function (i) {
        idx[$(this).text().trim()] = i;
    });

    table.find("tbody tr").each(function () {
        const cells = $(this).children();
        const d = data[cells.eq(0).text().trim()];
        if (!d) return;
        set_cell(cells.eq(idx["Total Allocated Leaves"]), d.accrued_to_date);
        set_cell(cells.eq(idx["Used Leaves"]), d.used);
        set_cell(cells.eq(idx["Leaves Pending Approval"]), d.pending);
        set_cell(cells.eq(idx["Available Leaves"]), d.available_now);
    });
}

// Only write when the value differs, so our own edit doesn't retrigger the observer.
function set_cell(cell, value) {
    if (cell.text().trim() !== String(value)) cell.text(value);
}

function start_watching(frm) {
    if (frm.__orion_observer) return;
    const target = form_root(frm).get(0);
    if (!target) return;

    frm.__orion_observer = new MutationObserver(() => {
        frm.__orion_observer.disconnect();
        apply(frm);
        frm.__orion_observer.observe(target, { childList: true, subtree: true });
    });
    frm.__orion_observer.observe(target, { childList: true, subtree: true });
}