// Copyright (c) 2025, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle Movement", {
    setup(frm) {
        // Only Idle, Active vehicles can start a new rental.
        frm.set_query("vehicle", () => ({
            filters: { custom_state: "Idle", custom_status: "Active" }
        }));
    },

    project_to(frm) {
        // Auto-fill Customer from the project when it has one — but keep it editable
        // so a project without a customer can still have one entered manually.
        if (!frm.doc.project_to || frm.doc.customer) return;
        frappe.db.get_value("Project", frm.doc.project_to, "customer").then((r) => {
            if (r && r.message && r.message.customer) {
                frm.set_value("customer", r.message.customer);
            }
        });
    },

    refresh(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.rental_status === "Active") {
            frm.add_custom_button(__("Demobilize"), () => {
                frappe.prompt(
                    [{
                        fieldname: "demobilize_date",
                        label: __("Demobilize Date"),
                        fieldtype: "Date",
                        reqd: 1,
                        default: frappe.datetime.get_today()
                    }],
                    (values) => {
                        frappe.call({
                            method: "orion_erp.orion_erp.doctype.vehicle_movement.vehicle_movement.demobilize",
                            args: { name: frm.doc.name, demobilize_date: values.demobilize_date },
                            freeze: true,
                            freeze_message: __("Demobilizing…"),
                            callback: () => frm.reload_doc()
                        });
                    },
                    __("Demobilize Vehicle"),
                    __("Confirm")
                );
            });
        }
    },
});
