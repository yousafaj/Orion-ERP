// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("LOA", {
    refresh: function(frm) {
        // Live-update the remaining quota when a CICPA changes this LOA, so no
        // manual refresh is needed. Register the listener once per form.
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
