// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Driver Movement", {

     driver(frm) {
        if (frm.doc.driver) {
            frappe.db.get_doc("Driver", frm.doc.driver).then(driver_doc => {
                if (driver_doc.employee) {
                    frappe.db.get_doc("Employee", driver_doc.employee).then(employee_doc => {
                        frm.set_value("employment_type", employee_doc.employment_type);
                    });
                }
            });
        }
    },

    // mobilization_status(frm) {
    //     if (frm.doc.mobilization_status) {
    //         console.log("new mobilization_status",frm.doc.mobilization_status);
    //         frm.set_query("driver", () => {
    //             if (frm.doc.mobilization_status === "Mobilize") {
    //                 return {
    //                     filters: {
    //                         custom_state: "Idle",
    //                         status: "Active"
    //                     }
    //                 };
    //             } else if (frm.doc.mobilization_status === "Demobilize") {
    //                 return {
    //                     filters: {
    //                         custom_state: "With Client",
    //                         status: "Active"
    //                     }
    //                 };
    //             }                
    //         });
    //     }
    // },

    mobilization_status(frm) {
    if (frm.doc.mobilization_status) {
        frappe.call({
            method: "rental_management.rental_management.doctype.driver_movement.utils.get_available_drivers",
            args: {
                mobilization_status: frm.doc.mobilization_status
            },
            callback: function(r) {
                if (r.message) {
                    const options = r.message.map(driver => ({
                        value: driver.name,
                        label: driver.label
                    }));

                    frm.set_query("driver", () => {
                        return {
                            filters: [
                                ["name", "in", options.map(d => d.value)]
                            ]
                        };
                    });

                }
            }
        });
    }
},


	refresh(frm) {

	},
});
