frappe.ui.form.on("Driver Movement", {
    setup(frm) {
        frm.set_query("vehicle_movement", () => ({filters: {docstatus: 1, rental_status: "Active"}}));
        frm.set_query("driver", () => ({filters: [
            ["Employee", "status", "=", "Active"],
            ["Employee", "custom_employee_category", "=", "Non-Office"],
            ["Employee", "designation", "like", "%Driver%"]
        ]}));
    },
    vehicle_movement(frm) {
        if (!frm.doc.vehicle_movement) return;
        frappe.db.get_value("Vehicle Movement", frm.doc.vehicle_movement,
            ["vehicle", "driver", "project_to"]).then((r) => {
            if (r.message) frm.set_value({vehicle: r.message.vehicle,
                previous_driver: r.message.driver || "", project: r.message.project_to || ""});
        });
    },
    mobilization_status(frm) {
        if (frm.doc.mobilization_status === "Demobilize") frm.set_value("driver", "");
    }
});
