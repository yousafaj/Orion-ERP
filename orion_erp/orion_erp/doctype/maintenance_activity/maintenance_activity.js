// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Maintenance Activity", {
	existing_maintenance(frm) {
        if (!frm.doc.vehicle) {
            frappe.msgprint("Please select a Vehicle first.");
            return;
        }

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Driver Movement",
                filters: {
                    vehicle: frm.doc.vehicle,
                    mobilization_status: "Mobilize"
                },
                fields: ["name", "driver", "shift", "project", "creation"],
                order_by: "creation desc",
                limit_page_length: 1
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    const last_mob = r.message[0];
                    frm.set_value("driver", last_mob.driver);
                    frm.set_value("shift", last_mob.shift);
                    frm.set_value("project", last_mob.project);
                } else {
                    frappe.msgprint("No Mobilization record found for this vehicle.");
                }
            }
        });
    },

    vehicle(frm) {
        if (frm.doc.existing_maintenance == 1) {
            frm.events.existing_maintenance(frm); 
        }
    }
});
