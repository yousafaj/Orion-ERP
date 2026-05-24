// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("LOA", {
    refresh: function(frm) {
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
		// if (!frm.doc.__islocal) return;
		frm.set_value("remaining_vehicle_quota", frm.doc.total_vehicle_quota || 0);
	},

	total_driver_quota: function(frm) {
		// if (!frm.doc.__islocal) return;
		frm.set_value("remaining_driver_quota", frm.doc.total_driver_quota || 0);
	}
});
