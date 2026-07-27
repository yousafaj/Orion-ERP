// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("LEAVE DECLARATION", {

    setup: function(frm) {
        frm.set_query("employee", function() {
            return {
                filters: { status: "Active" }
            };
        });

        frm.set_query("leave_type", function() {
            return {
                filters: { is_lwp: 0 }
            };
        });

        frm.set_query("leave_application", function() {
            let filters = {
                docstatus: 1,
                custom_approval_status: "Approved",
            };
            if (frm.doc.employee) {
                filters.employee = frm.doc.employee;
            }
            return {
                filters: filters,
                query: "orion_erp.orion_erp.doctype.leave_declaration.leave_declaration.get_available_leave_applications",
            };
        });
    },

    leave_application: function(frm) {
        if (!frm.doc.leave_application) {
            return;
        }
        frappe.call({
            method: "orion_erp.orion_erp.doctype.leave_declaration.leave_declaration.get_leave_application_data",
            args: { leave_application: frm.doc.leave_application },
            callback: function(r) {
                if (r.message) {
                    let d = r.message;
                    frm.set_value("employee", d.employee);
                    frm.set_value("employee_name", d.employee_name);
                    frm.set_value("company", d.company);
                    frm.set_value("leave_type", d.leave_type);
                    frm.set_value("leave_start_date", d.leave_start_date);
                    frm.set_value("leave_end_date", d.leave_end_date);
                    frm.set_value("leaving_date", d.leaving_date);
                    frm.set_value("designation", d.designation);
                    frm.set_value("passport_number", d.passport_number);

                    if (d.total_leave_days !== undefined) {
                        frm.set_value("leave_days", d.total_leave_days);
                    }

                    frappe.call({
                        method: "orion_erp.orion_erp.doctype.leave_declaration.leave_declaration.get_employee_asset_details",
                        args: { employee: d.employee },
                        callback: function(r) {
                            frm.clear_table("asset_clearance_detail");
                            if (r.message && r.message.length) {
                                r.message.forEach(function(asset) {
                                    let row = frm.add_child("asset_clearance_detail", {
                                        asset_type: asset.asset_type,
                                        asset_code: asset.asset_code,
                                        issued_by: asset.issued_by,
                                        issued_date: asset.issued_date,
                                        attachment_upload: asset.attachment_upload,
                                        asset_status: asset.asset_status,
                                        qty: asset.qty,
                                        return_date: asset.return_date,
                                        sim_card_number: asset.sim_card_number,
                                        network: asset.network,
                                        sim_status: asset.sim_status,
                                        brand: asset.brand,
                                        model: asset.model,
                                        imei_number: asset.imei_number,
                                        sim_number: asset.sim_number,
                                        network_provider: asset.network_provider,
                                        condition: asset.condition,
                                        vehicle_type: asset.vehicle_type,
                                        brand_model: asset.brand_model,
                                        plate_number: asset.plate_number,
                                        vehicle_cicpa_pass: asset.vehicle_cicpa_pass,
                                        fuel_type: asset.fuel_type,
                                        mulkiya_expiry_uae_specific: asset.mulkiya_expiry_uae_specific,
                                        odometer_reading_at_issue: asset.odometer_reading_at_issue,
                                        odometer_reading_at_return: asset.odometer_reading_at_return,
                                        name_of_last_user: asset.name_of_last_user,
                                        device_type: asset.device_type,
                                        it_brand: asset.it_brand,
                                        it_model: asset.it_model,
                                        attachment: asset.attachment,
                                        card_number: asset.card_number,
                                        card_issue_date: asset.card_issue_date,
                                        lost__reissued: asset.lost__reissued,
                                        pass_number: asset.pass_number,
                                        valid_to: asset.valid_to,
                                        cicpa_status: asset.cicpa_status,
                                        linked_account: asset.linked_account,
                                        expiry_date: asset.expiry_date,
                                        request_date: asset.request_date,
                                        parking_status: asset.parking_status,
                                        parking_slot_number: asset.parking_slot_number,
                                        source_asset_handover: asset.parent,
                                        source_asset_handover_detail: asset.name,
                                    });
                                });
                            }
                            frm.refresh_field("asset_clearance_detail");
                        }
                    });

                    frappe.call({
                        method: "orion_erp.orion_erp.doctype.leave_declaration.leave_declaration.get_leave_balance",
                        args: {
                            employee: d.employee,
                            leave_type: d.leave_type,
                            date: d.leave_start_date
                        },
                        callback: function(r) {
                            if (r.message !== undefined) {
                                frm.set_value("leave_balance_before", r.message || 0);
                            }
                        }
                    });

                    frappe.call({
                        method: "orion_erp.orion_erp.doctype.leave_declaration.leave_declaration.get_outstanding_advance",
                        args: { employee: d.employee },
                        callback: function(r) {
                            if (r.message !== undefined) {
                                frm.set_value("outstanding_advance", r.message || 0);
                            }
                        }
                    });
                }
            }
        });
    },

    leave_start_date: function(frm) {
        if (frm.doc.employee && frm.doc.leave_type && frm.doc.leave_start_date) {
            frappe.call({
                method: "orion_erp.orion_erp.doctype.leave_declaration.leave_declaration.get_leave_balance",
                args: {
                    employee: frm.doc.employee,
                    leave_type: frm.doc.leave_type,
                    date: frm.doc.leave_start_date
                },
                callback: function(r) {
                    frm.set_value("leave_balance_before", r.message || 0);
                }
            });
        }
    },

    leave_end_date: function(frm) {
    },

});

frappe.ui.form.on("Leave Declaration Asset Clearance Detail", {
    asset_status: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.asset_status === "Returned" && !row.return_date) {
            frappe.msgprint(__("Return Date is mandatory when Asset Status is Returned."));
        }
    },
});
