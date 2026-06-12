// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("LOA", {
    refresh: function(frm) {
        // Always pull the latest quota counters from the DB whenever the LOA is
        // shown — the route cache can serve stale values after a CICPA was created
        // (and you navigated away and back). This needs no realtime/socketio.
        if (frm.doc.name && !frm.is_new() && !frm.is_dirty()) {
            const qfields = [
                "remaining_vehicle_quota", "remaining_driver_quota",
                "total_created_vehicle_cicpa", "total_created_driver_cicpa",
                "total_cancelled_vehicle_cicpa", "total_cancelled_driver_cicpa",
            ];
            frappe.db.get_value("LOA", frm.doc.name, qfields).then((r) => {
                const v = (r && r.message) || {};
                let changed = false;
                qfields.forEach((f) => {
                    if (v[f] !== undefined && frm.doc[f] !== v[f]) {
                        frm.doc[f] = v[f];
                        frm.refresh_field(f);
                        changed = true;
                    }
                });
                if (changed) frm.dashboard.clear_comment();
            });
        }

        // Also live-update when the LOA form is open while a CICPA changes it.
        if (!frm.__loa_quota_listener) {
            frm.__loa_quota_listener = true;
            frappe.realtime.on("orion_loa_quota_updated", function(data) {
                if (data && data.loa === frm.doc.name && !frm.is_dirty()) {
                    frm.reload_doc();
                }
            });
        }

        if (frm.doc.docstatus === 1) {

            if (frm.doc.total_created_vehicle_cicpa < frm.doc.total_vehicle_quota) {
                frm.add_custom_button(__('Vehicle CICPA'), function() {
                    frappe.new_doc("CICPA", {
                        loa: frm.doc.name,
                        cicpa_type: "Vehicle"
                    });
                }, __("Create"));
            }

            if (frm.doc.total_created_driver_cicpa < frm.doc.total_driver_quota) {
                frm.add_custom_button(__('Driver CICPA'), function() {
                    frappe.new_doc("CICPA", {
                        loa: frm.doc.name,
                        cicpa_type: "Driver"
                    });
                }, __("Create"));
            }

        }
    },

    total_vehicle_quota: function(frm) {
		// remaining = total − already-created, so editing the quota after some
		// CICPAs exist doesn't wipe the consumption already recorded.
		frm.set_value(
			"remaining_vehicle_quota",
			(frm.doc.total_vehicle_quota || 0) - (frm.doc.total_created_vehicle_cicpa || 0)
		);
	},

	total_driver_quota: function(frm) {
		frm.set_value(
			"remaining_driver_quota",
			(frm.doc.total_driver_quota || 0) - (frm.doc.total_created_driver_cicpa || 0)
		);
	}
});

frappe.ui.form.on("LOA locations cdt", {
	location: function (frm, cdt, cdn) {
		// Auto-fill the row's Location Code from the Location (still editable, so a
		// blank one can be typed in and is saved back to the Location on save).
		const row = locals[cdt][cdn];
		if (!row.location) return;
		frappe.db.get_value("Location", row.location, "custom_location_code").then((r) => {
			if (r && r.message && r.message.custom_location_code) {
				frappe.model.set_value(cdt, cdn, "location_code", r.message.custom_location_code);
			}
		});
	},
});
