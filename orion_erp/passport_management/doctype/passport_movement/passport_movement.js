// Client Script — Passport Movement
// Handles UI behaviour: auto-fetch, naming series, quick actions, validations.

frappe.ui.form.on('Passport Movement', {

    // ── Form lifecycle ────────────────────────────────────────────────────────

    setup(frm) {
        frm.set_query('employee', () => ({ filters: { status: 'Active' } }));
        frm.set_query('received_by', () => ({ filters: { enabled: 1 } }));
    },

    refresh(frm) {
        // Fetched / system fields are always read-only
        ['employee_name', 'passport_number', 'department', 'designation', 'is_active_record', 'actual_return_date']
            .forEach(f => frm.set_df_property(f, 'read_only', 1));

        if (frm.doc.docstatus === 1) {
            _add_action_buttons(frm);
        }

        _highlight_overdue(frm);
    },

    // ── Field events ──────────────────────────────────────────────────────────

    movement_type(frm) {
        const seriesMap = {
            'In':  'PM-IN-.YYYY.-.#####',
            'Out': 'PM-OUT-.YYYY.-.#####',
        };
        if (seriesMap[frm.doc.movement_type]) {
            frm.set_value('naming_series', seriesMap[frm.doc.movement_type]);
        }

        // Sensible status defaults
        if (frm.doc.movement_type === 'In' && !frm.doc.current_status) {
            frm.set_value('current_status', 'With Company');
        } else if (frm.doc.movement_type === 'Out' && !frm.doc.current_status) {
            frm.set_value('current_status', 'Returned to Employee');
        }

        // Warn if Out has no active In
        if (frm.doc.movement_type === 'Out' && frm.doc.employee) {
            _check_active_in(frm);
        }
    },

    employee(frm) {
        if (!frm.doc.employee) {
            ['employee_name', 'passport_number', 'department', 'designation']
                .forEach(f => frm.set_value(f, ''));
            return;
        }

        // Standard Employee fields (top-level on Employee doctype)
        frappe.db.get_value(
            'Employee',
            frm.doc.employee,
            ['employee_name', 'department', 'designation'],
            r => {
                if (!r) return;
                frm.set_value('employee_name', r.employee_name);
                frm.set_value('department',    r.department);
                frm.set_value('designation',   r.designation);
            }
        );

        // Passport number: resolved server-side because it may live in a
        // Certificates child table, not as a top-level Employee field.
        frappe.call({
            method: 'orion_erp.passport_management.doctype.passport_movement.passport_movement.get_employee_passport',
            args: { employee: frm.doc.employee },
            callback(r) {
                if (r && r.message) {
                    frm.set_value('passport_number', r.message.passport_number || '');
                }
            },
        });

        // Check for active IN when movement_type is Out
        if (frm.doc.movement_type === 'Out') {
            _check_active_in(frm);
        }
    },

    expected_return_date(frm) {
        if (frm.doc.expected_return_date && frm.doc.transaction_date) {
            if (frm.doc.expected_return_date < frm.doc.transaction_date) {
                frappe.msgprint({
                    message: __('Expected Return Date should not be before Transaction Date.'),
                    indicator: 'orange',
                    title: __('Date Warning'),
                });
                frm.set_value('expected_return_date', '');
            }
        }
    },
});

// ── Private helpers ───────────────────────────────────────────────────────────

function _check_active_in(frm) {
    frappe.call({
        method: 'orion_erp.passport_management.doctype.passport_movement.passport_movement.get_active_in_record',
        args: { employee: frm.doc.employee },
        callback(r) {
            if (!r.message) {
                frappe.msgprint({
                    message: __(
                        'No active Passport IN record found for this employee. '
                        + 'An OUT movement requires a prior submitted IN record.'
                    ),
                    indicator: 'red',
                    title: __('Missing IN Record'),
                });
            } else {
                frappe.show_alert({
                    message: __('Active IN record: {0}', [r.message.name]),
                    indicator: 'green',
                });
            }
        },
    });
}

function _add_action_buttons(frm) {
    // Quick shortcut to create the corresponding OUT movement
    if (frm.doc.movement_type === 'In' && frm.doc.is_active_record) {
        frm.add_custom_button(__('Create OUT Movement'), () => {
            frappe.new_doc('Passport Movement', {
                employee:      frm.doc.employee,
                movement_type: 'Out',
            });
        }, __('Actions'));
    }

    // Print passport receipt
    frm.add_custom_button(__('Print Receipt'), () => {
        frappe.route_options = { doctype: 'Passport Movement', name: frm.doc.name };
        frappe.set_route('print', 'Passport Movement', frm.doc.name);
    }, __('Actions'));
}

function _highlight_overdue(frm) {
    if (
        frm.doc.movement_type === 'In'
        && frm.doc.is_active_record
        && frm.doc.expected_return_date
        && frm.doc.expected_return_date < frappe.datetime.get_today()
    ) {
        frm.dashboard.set_headline(
            __('⚠ Passport overdue since {0}', [frappe.datetime.str_to_user(frm.doc.expected_return_date)]),
            'red'
        );
    }
}
