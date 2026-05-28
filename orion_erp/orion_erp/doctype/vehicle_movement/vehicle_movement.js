// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle Movement", {

    vehicle(frm) {
        if (frm.doc.vehicle) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Vehicle",
                    filters: { name: frm.doc.vehicle },
                    fieldname: "custom_project"
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value("project_id", r.message.custom_project);
                    }
                }
            });
        }
        else{
            frm.set_value("project_id", null);
        }
    },

    status(frm) {
        if (frm.doc.status) {
            frm.set_query("vehicle", () => {
                if (frm.doc.status === "Mobilise") {
                    return {
                        filters: {
                            custom_state: "Idle",
                            custom_status: "Active"
                        }
                    };
                } else if (frm.doc.status === "Demobilise") {
                    return {
                        filters: {
                            custom_state: "With Client",
                            custom_status: "Active"
                        }
                    };
                }
                else if (frm.doc.status === "Breakdown") {
                    return {
                        filters: [
                            ["custom_status", "=", "Active"]
                        ]
                    };
                }
                else if (frm.doc.status === "Available for Use") {
                    return {
                        filters: {
                            custom_state: "Workshop",
                            custom_status: "Active"
                        }
                    };
                }
            });
        }
    },
});
