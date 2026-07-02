frappe.ui.form.on('Leave Allocation', {
    refresh: function(frm) {
        let excess = flt(frm.doc.custom_excess_leave_days);
        if (excess <= 0) return;

        if (frm.doc.docstatus === 0) {
            lock_excess_fields(frm);
            let status = frm.doc.custom_excess_leave_status || 'Pending';
            if (status === 'Pending') {
                show_excess_dialog(frm, excess);
            }
        }

        if (frm.doc.docstatus === 1 && excess > 0) {
            lock_excess_fields(frm);
            let status = frm.doc.custom_excess_leave_status || 'Pending';
            frm.dashboard.add_comment(
                __('Excess Leave: {0} days — {1}', [excess, status]),
                'orange', true
            );
        }
    },

    before_submit: function(frm) {
        let excess = flt(frm.doc.custom_excess_leave_days);
        if (excess <= 0) return;

        let status = frm.doc.custom_excess_leave_status || 'Pending';
        if (status === 'Pending') {
            frappe.validated = false;
            show_excess_dialog(frm, excess);
            frappe.throw(__('Please complete the excess leave decision.'));
        }
        if (status === 'Extend') {
            let cf_days = flt(frm.doc.custom_carry_forward_days);
            let lapsed_days = flt(frm.doc.custom_lapsed_leave_days);
            if (cf_days <= 0) {
                frappe.validated = false;
                frappe.throw(__('Carry Forward Days must be greater than 0'));
            }
            if (cf_days > excess) {
                frappe.validated = false;
                frappe.throw(__('Carry Forward Days ({0}) cannot exceed Excess Leave Days ({1})', [cf_days, excess]));
            }
            if (flt(cf_days + lapsed_days) !== excess) {
                frappe.validated = false;
                frappe.throw(__('Carry Forward Days ({0}) + Lapsed Days ({1}) must equal Excess Leave Days ({2})', [cf_days, lapsed_days, excess]));
            }
        }
    }
});

function lock_excess_fields(frm) {
    frm.set_df_property('new_leaves_allocated', 'read_only', 1);
    frm.set_df_property('custom_excess_leave_status', 'hidden', 1);
    frm.set_df_property('custom_carry_forward_days', 'read_only', 1);
    frm.set_df_property('custom_excess_leave_days', 'read_only', 1);
    frm.set_df_property('custom_lapsed_leave_days', 'read_only', 1);
    frm.set_df_property('custom_decision_date', 'read_only', 1);
    frm.set_df_property('custom_decided_by', 'read_only', 1);
}

function show_excess_dialog(frm, excess) {
    let dialog = new frappe.ui.Dialog({
        title: __('Excess Leave Decision Required'),
        minimizable: false,
        fields: [
            {
                fieldname: 'info_html',
                fieldtype: 'HTML',
                options: __(
                    '<div style="padding:12px;background:#fff3e0;border:1px solid #ffcc80;border-radius:4px;margin-bottom:8px;">' +
                    '<b style="font-size:14px;">⚠ Excess Leave Detected</b><br><br>' +
                    'This employee has <b>{0}</b> excess leave days that exceed the carry-forward limit.<br>' +
                    'Please decide whether to carry forward or lapse these excess days.' +
                    '</div>',
                    [excess]
                )
            },
            {
                fieldname: 'action_type',
                label: __('Action'),
                fieldtype: 'Select',
                default: 'Carry Forward',
                options: [
                    { value: 'Carry Forward', label: __('Carry Forward — transfer some/all excess to next year') },
                    { value: 'Lapse All', label: __('Lapse All — forfeit all excess days') }
                ],
                onchange: function() {
                    let val = this.get_value();
                    dialog.get_field('carry_forward_days').df.hidden = (val !== 'Carry Forward');
                    dialog.get_field('carry_forward_days').refresh();
                    dialog.get_field('lapsed_note').df.hidden = (val !== 'Lapse All');
                    dialog.get_field('lapsed_note').refresh();
                }
            },
            {
                fieldname: 'carry_forward_days',
                label: __('Days to Carry Forward'),
                fieldtype: 'Float',
                non_negative: 1,
                default: excess,
                description: __('Between 1 and {0}', [excess]),
                hidden: 0
            },
            {
                fieldname: 'lapsed_note',
                fieldtype: 'HTML',
                hidden: 1,
                options: __(
                    '<div style="padding:8px;background:#fce4ec;border:1px solid #ef9a9a;border-radius:4px;">' +
                    'All <b>{0}</b> excess days will be lapsed (forfeited). No additional leave will be credited.' +
                    '</div>',
                    [excess]
                )
            },
            { fieldtype: 'Column Break' },
            {
                fieldname: 'remarks',
                label: __('Remarks'),
                fieldtype: 'Small Text'
            },
            { fieldtype: 'Section Break' },
            {
                fieldname: 'decision_info',
                fieldtype: 'HTML',
                options: __('Decision will be recorded with today\'s date and your user ID.')
            }
        ],
        primary_action_label: __('Confirm & Submit'),
        primary_action: function(values) {
            let action = values.action_type;
            let cf_days = flt(values.carry_forward_days);
            let lapsed_days;

            if (action === 'Carry Forward') {
                if (cf_days <= 0) {
                    frappe.msgprint(__('Enter the number of days to carry forward (minimum 1).'));
                    return;
                }
                if (cf_days > excess) {
                    frappe.msgprint(__('Cannot carry forward {0} days. Maximum excess: {1}', [cf_days, excess]));
                    return;
                }
                lapsed_days = excess - cf_days;
                let new_total = flt(frm.doc.new_leaves_allocated) + cf_days;

                frm.set_value('new_leaves_allocated', new_total);
                frm.set_value('custom_excess_leave_status', 'Extend');
                frm.set_value('custom_carry_forward_days', cf_days);
                frm.set_value('custom_lapsed_leave_days', lapsed_days);
            } else {
                lapsed_days = excess;
                frm.set_value('custom_excess_leave_status', 'Forfeit');
                frm.set_value('custom_lapsed_leave_days', lapsed_days);
            }

            frm.set_value('custom_decision_date', frappe.datetime.get_today());
            frm.set_value('custom_decided_by', frappe.session.user);
            frm.set_value('custom_excess_leave_remarks', values.remarks);

            dialog.hide();
            lock_excess_fields(frm);
            frm.save_or_update().then(() => {
                frm.savesubmit().then(() => {
                    let msg = action === 'Carry Forward'
                        ? __('{0} days carried forward, {1} days lapsed', [cf_days, lapsed_days])
                        : __('All {0} excess days lapsed', [excess]);
                    frappe.show_alert({ message: msg, indicator: action === 'Carry Forward' ? 'green' : 'red' });
                });
            });
        }
    });

    dialog.$wrapper.find('.modal-header .close').hide();
    dialog.show();
}
