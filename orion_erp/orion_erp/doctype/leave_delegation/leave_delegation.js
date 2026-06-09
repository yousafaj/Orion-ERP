function fetch_pending_workflows(frm) {
    if (!frm.doc.delegator_user || !frm.doc.valid_from || !frm.doc.valid_to) return;

    frappe.call({
        method: "orion_erp.orion_erp.doctype.leave_delegation.leave_delegation.get_pending_workflows",
        args: {
            delegator: frm.doc.delegator_user,
            valid_from: frm.doc.valid_from,
            valid_to: frm.doc.valid_to,
        },
        callback: function (r) {
            if (!r.message) return;

            frm.clear_table("leave_delegation_detail");
            r.message.forEach(function (row) {
                let child = frm.add_child("leave_delegation_detail");
                child.document_name = row.document_name;
                child.level = row.level;
                child.approver_field = row.approver_field;
                child.previous_reviewer = row.previous_reviewer;
                child.delegate_user = frm.doc.delegate_user || "";
                child.has_delegation = 1;
            });
            frm.refresh_field("leave_delegation_detail");
        },
    });
}

function check_overlap(frm) {
    if (!frm.doc.delegator_user || !frm.doc.valid_from || !frm.doc.valid_to) return;

    frappe.call({
        method: "orion_erp.orion_erp.doctype.leave_delegation.leave_delegation.check_overlapping_delegation",
        args: {
            delegator_user: frm.doc.delegator_user,
            valid_from: frm.doc.valid_from,
            valid_to: frm.doc.valid_to,
            name: frm.doc.name,
        },
        callback: function (r) {
            if (r.message) {
                frappe.msgprint({
                    title: __("Overlapping Delegation"),
                    indicator: "orange",
                    message: __("An active Leave Delegation already exists for {0} with overlapping dates. Please adjust the dates.").format(frm.doc.delegator_user),
                });
            }
        },
    });
}

frappe.ui.form.on("Leave Delegation", {
    delegator_user: function (frm) {
        frm.clear_table("leave_delegation_detail");
        frm.refresh_field("leave_delegation_detail");
    },
    valid_from: function (frm) {
        if (frm.doc.valid_from && frm.doc.valid_to && frm.doc.valid_from > frm.doc.valid_to) {
            frappe.msgprint(__("Valid From cannot be later than Valid To"));
            return;
        }
        check_overlap(frm);
        fetch_pending_workflows(frm);
    },
    valid_to: function (frm) {
        if (frm.doc.valid_from && frm.doc.valid_to && frm.doc.valid_from > frm.doc.valid_to) {
            frappe.msgprint(__("Valid To cannot be earlier than Valid From"));
            return;
        }
        check_overlap(frm);
        fetch_pending_workflows(frm);
    },
    delegate_user: function (frm) {
        if (!frm.doc.delegate_user) return;

        $.each(frm.doc.leave_delegation_detail || [], function (i, row) {
            frappe.model.set_value(row.doctype, row.name, "delegate_user", frm.doc.delegate_user);
        });
        frm.refresh_field("leave_delegation_detail");
    },
    refresh: function (frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Restore Original Approvers"), function () {
                frappe.call({
                    method: "frappe.client.cancel",
                    args: {
                        doctype: "Leave Delegation",
                        name: frm.doc.name,
                    },
                    callback: function () {
                        frappe.msgprint(__("Delegation cancelled and approvers restored"));
                        frm.reload_doc();
                    },
                });
            });
        }
    },
});
