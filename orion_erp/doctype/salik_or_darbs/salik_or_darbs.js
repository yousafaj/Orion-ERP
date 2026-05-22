frappe.ui.form.on("Salik or Darbs", {
        post_salik(frm) {
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
        if (frm.doc.post_salik == 1) {
            frm.events.post_salik(frm); 
        }
    }
});

frappe.ui.form.on("Fines cdt", {
    detail_add: function(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);

        if (frm.doc.project) {
            row.project = frm.doc.project;
        }

        if (frm.doc.vehicle) {
            row.vrn = frm.doc.vehicle;
        }

        frm.refresh_field("detail");
    }
});