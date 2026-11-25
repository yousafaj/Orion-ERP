// File: apps/orion_erp/orion_erp/orion_erp/doctype/mobilization_order/mobilization_order.js
// Replace the WHOLE content of the file with this.

const API = "orion_erp.orion_erp.validations.fleet_oprations.";

// Fill Driver Name / Vehicle Type immediately when a Driver / Vehicle is picked in a row
frappe.ui.form.on("Mobilization Order Vehicle", {
	driver(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.driver) {
			frappe.model.set_value(cdt, cdn, "driver_name", "");
			return;
		}
		frappe
			.call({ method: API + "get_driver_name", args: { driver: row.driver } })
			.then((r) => frappe.model.set_value(cdt, cdn, "driver_name", r.message || ""));
	},
	vehicle(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.vehicle) return;
		frappe.db
			.get_value("Vehicle", row.vehicle, "custom_vehicle_type")
			.then((r) => frappe.model.set_value(cdt, cdn, "vehicle_type", (r.message || {}).custom_vehicle_type || ""));
	},
});

frappe.ui.form.on("Mobilization Order", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Get Vehicles"), () => pick_vehicles(frm));
			frm.add_custom_button(__("Get Drivers"), () => pick_drivers(frm));
		}

		if (frm.doc.docstatus === 1) {
			const pending = (frm.doc.vehicles || []).some((r) => !r.deployment);
			if (pending) {
				frm.add_custom_button(__("Create Deployments"), () => create_deployments(frm)).addClass(
					"btn-primary"
				);
			}
			frm.add_custom_button(__("Replace Driver"), () => replace(frm, "driver"), __("Actions"));
			frm.add_custom_button(__("Replace Vehicle"), () => replace(frm, "vehicle"), __("Actions"));
			frm.add_custom_button(__("Demobilize Order"), () => demobilize(frm), __("Actions"));
			// frm.add_custom_button(__("Transfer to Another Site"), () => transfer_site(frm), __("Actions"));
			frm.add_custom_button(__("Swap with Another Site"), () => swap_assignments(frm), __("Actions"));

		}
	},
});

// ---------- a simple "tick the items" dialog with search ----------
function pick_dialog(title, items, on_ok) {
	const rows = items
		.map(
			(i) =>
				`<div class="pick-row" style="padding:4px 0;">
					<label style="font-weight:normal;cursor:pointer;">
						<input type="checkbox" class="pick-cb" data-value="${frappe.utils.escape_html(i.value)}">
						&nbsp;${frappe.utils.escape_html(i.label)}
					</label>
				</div>`
		)
		.join("");

	const d = new frappe.ui.Dialog({
		title: title,
		fields: [
			{ fieldname: "search", fieldtype: "Data", label: __("Search") },
			{
				fieldname: "list",
				fieldtype: "HTML",
				options: `<div style="max-height:380px;overflow:auto;">${rows}</div>`,
			},
		],
		primary_action_label: __("Add Selected"),
		primary_action() {
			const selected = [];
			d.$wrapper.find("input.pick-cb:checked").each(function () {
				selected.push($(this).attr("data-value"));
			});
			if (!selected.length) {
				frappe.msgprint(__("Tick at least one item."));
				return;
			}
			d.hide();
			on_ok(selected);
		},
	});
	d.show();
	d.fields_dict.search.$input.on("input", function () {
		const q = ($(this).val() || "").toLowerCase();
		d.$wrapper.find(".pick-row").each(function () {
			$(this).toggle($(this).text().toLowerCase().includes(q));
		});
	});
}

function pick_vehicles(frm) {
	frappe.call({ method: API + "get_free_vehicles" }).then((r) => {
		const used = (frm.doc.vehicles || []).map((row) => row.vehicle);
		const free = (r.message || []).filter((v) => !used.includes(v.value));
		if (!free.length) {
			frappe.msgprint(__("No free vehicles found."));
			return;
		}
		pick_dialog(__("Free Vehicles"), free, (selected) => {
			const empty = (frm.doc.vehicles || []).filter((row) => !row.vehicle);
			selected.forEach((v, i) => {
				const row = empty[i] || frm.add_child("vehicles");
				frappe.model.set_value(row.doctype, row.name, "vehicle", v);
			});
			frm.refresh_field("vehicles");
		});
	});
}

function pick_drivers(frm) {
	frappe.call({ method: API + "get_free_drivers" }).then((r) => {
		const used = (frm.doc.vehicles || []).map((row) => row.driver).filter(Boolean);
		const free = (r.message || []).filter((d) => !used.includes(d.value));
		if (!free.length) {
			frappe.msgprint(
				__("No free drivers found. Check the driver designation setting (DRIVER_DESIGNATIONS).")
			);
			return;
		}
		pick_dialog(__("Free Drivers"), free, (selected) => {
			// fills the empty Driver cells from top to bottom. You can change the pairing afterwards.
			const empty = (frm.doc.vehicles || []).filter((row) => !row.driver);
			selected.forEach((d, i) => {
				if (empty[i]) frappe.model.set_value(empty[i].doctype, empty[i].name, "driver", d);
			});
			if (selected.length > empty.length) {
				frappe.msgprint(
					__("{0} driver(s) were not placed because there are no empty rows. Add vehicles first.", [
						selected.length - empty.length,
					])
				);
			}
			frm.refresh_field("vehicles");
		});
	});
}

function create_deployments(frm) {
	frappe.confirm(__("Create a Vehicle Deployment for every row?"), () => {
		frappe.call({
			method: API + "create_deployments",
			args: { order: frm.doc.name },
			freeze: true,
			freeze_message: __("Creating deployments..."),
		}).then((r) => {
			frappe.show_alert({ message: __("{0} deployment(s) created", [r.message]), indicator: "green" });
			frm.reload_doc();
		});
	});
}

function replace(frm, kind) {
	const mobilized = (frm.doc.vehicles || []).filter((r) => r.status === "Mobilized" && r.deployment);
	if (!mobilized.length) {
		frappe.msgprint(__("There is no Mobilized row to replace."));
		return;
	}
	const method = kind === "driver" ? "get_free_drivers" : "get_free_vehicles";
	frappe.call({ method: API + method }).then((r) => {
		const free = r.message || [];
		if (!free.length) {
			frappe.msgprint(__("Nothing free to replace with."));
			return;
		}
		const d = new frappe.ui.Dialog({
			title: kind === "driver" ? __("Replace Driver") : __("Replace Vehicle"),
			fields: [
				{
					fieldname: "row",
					label: __("Row to change"),
					fieldtype: "Select",
					reqd: 1,
					options: [{ label: "", value: "" }].concat(
						mobilized.map((r) => ({
							label: `${r.idx}  |  Vehicle ${r.vehicle}  |  ${r.driver_name || r.driver || ""}`,
							value: r.name,
						}))
					),
				},
				{
					fieldname: "new_value",
					label: kind === "driver" ? __("New Driver") : __("New Vehicle"),
					fieldtype: "Select",
					options: [{ label: "", value: "" }].concat(free.map((i) => ({ label: i.label, value: i.value }))),
					reqd: 1,
				},
				{ fieldname: "reason", label: __("Reason"), fieldtype: "Small Text", reqd: 1 },
			],
			primary_action_label: __("Replace"),
			primary_action(values) {
				const args = { order: frm.doc.name, row_name: values.row, reason: values.reason };
				if (kind === "driver") args.new_driver = values.new_value;
				else args.new_vehicle = values.new_value;
				frappe.call({
					method: API + (kind === "driver" ? "replace_driver" : "replace_vehicle"),
					args: args,
					freeze: true,
				}).then(() => {
					d.hide();
					frappe.show_alert({ message: __("Replaced"), indicator: "green" });
					frm.reload_doc();
				});
			},
		});
		d.show();
	});
}

// In mobilization_order.js:
//  1. DELETE the old  function demobilize(frm) { ... }  (the last function in the file)
//  2. PASTE this at the bottom
//  3. (optional) rename the button in refresh():
//     frm.add_custom_button(__("Vehicle Status / Demobilize"), () => demobilize(frm), __("Actions"));

// function demobilize(frm) {
// 	frappe.call({ method: API + "get_order_vehicle_states", args: { order: frm.doc.name } }).then((res) => {
// 		const rows = res.message || [];
// 		if (!rows.length) {
// 			frappe.msgprint(__("This order has no vehicles."));
// 			return;
// 		}
// 		const esc = frappe.utils.escape_html;
// 		const choices = ["Available", "Idle", "Workshop"];
// 		const color = { "With Client": "blue", Available: "green", Idle: "orange", Workshop: "red" };

// 		const body = rows
// 			.map((r) => {
// 				const opts = (r.state === "With Client" ? [["With Client", __("Stay with client")]] : []).concat(
// 					choices.map((c) => [c, __(c)])
// 				);
// 				const select = `<select class="form-control input-sm dm-goes" data-current="${esc(r.state)}" ${
// 					r.locked ? "disabled" : ""
// 				}>${opts
// 					.map(([v, l]) => `<option value="${v}" ${v === r.state ? "selected" : ""}>${l}</option>`)
// 					.join("")}</select>`;
// 				return `<tr data-row="${esc(r.row_name)}">
// 					<td style="vertical-align:middle"><b>${esc(r.vehicle)}</b></td>
// 					<td style="vertical-align:middle">${esc(r.driver_name)}</td>
// 					<td style="vertical-align:middle"><span class="indicator-pill ${color[r.state] || "gray"}">${__(r.state)}</span>${
// 						r.locked ? `<div class="text-muted small">${__("working on another job")}</div>` : ""
// 					}</td>
// 					<td>${select}</td>
// 					<td><input type="date" class="form-control input-sm dm-from" max="${frappe.datetime.get_today()}" value="${frappe.datetime.get_today()}" disabled></td>
// 					<td><input class="form-control input-sm dm-reason" placeholder="${__("Reason")}" disabled></td>
// 					<td><input class="form-control input-sm dm-workshop" placeholder="${__("Workshop name")}" disabled></td>
// 				</tr>`;
// 			})
// 			.join("");

// 		const table = `
// 			<table class="table table-bordered" style="font-size:13px;">
// 				<thead><tr>
// 					<th style="width:12%">${__("Vehicle")}</th>
// 					<th style="width:17%">${__("Driver")}</th>
// 					<th style="width:15%">${__("Now")}</th>
// 					<th style="width:17%">${__("Change to")}</th>
// 					<th style="width:12%">${__("From Date")} *</th>
// 					<th style="width:23%">${__("Reason (needed for Workshop)")}</th>
// 					<th style="width:16%">${__("Workshop")}</th>
// 				</tr></thead>
// 				<tbody>${body}</tbody>
// 			</table>`;

// 		const d = new frappe.ui.Dialog({
// 			title: __("Vehicle Status / Demobilize"),
// 			size: "extra-large",
// 			fields: [
// 				{
// 					fieldtype: "HTML",
// 					options: `<p class="text-muted">${__(
// 						"Choose the new status only for the vehicles you want to change. A vehicle in the workshop must be moved to Idle or Available before it can be used by another customer."
// 					)}</p>`,
// 				},
// 				{
// 					fieldname: "all",
// 					label: __("Set all vehicles to"),
// 					fieldtype: "Select",
// 					options: "\nAvailable\nIdle\nWorkshop",
// 					change() {
// 						const v = d.get_value("all");
// 						if (!v) return;
// 						d.$wrapper.find("select.dm-goes:not(:disabled)").each(function () {
// 							if ($(this).find(`option[value="${v}"]`).length) $(this).val(v).trigger("change");
// 						});
// 					},
// 				},
// 				{ fieldtype: "HTML", fieldname: "grid", options: table },
// 			],
// 			primary_action_label: __("Apply"),
// 			primary_action() {
// 				const moves = [];
// 				let missing = null;
// 				d.$wrapper.find("tr[data-row]").each(function () {
// 					const $r = $(this);
// 					const $s = $r.find("select.dm-goes");

// 					const goes = $s.val();
// 					if (!goes || goes === $s.attr("data-current")) return; // unchanged row
// 					const m = {
// 						row_name: $r.attr("data-row"),
// 						goes_to: goes,
// 						from_date: $r.find(".dm-from").val(),

// 						reason: ($r.find(".dm-reason").val() || "").trim(),
// 						workshop_name: ($r.find(".dm-workshop").val() || "").trim(),
// 					};
// 					if (goes === "Workshop" && !m.reason && !missing) missing = $r.find("td:first").text();
// 					moves.push(m);
// 				});
// 				if (!moves.length) {
// 					frappe.msgprint(__("Nothing to change. Every vehicle already has this status."));
// 					return;
// 				}
// 				if (missing) {
// 					frappe.msgprint(__("Vehicle {0}: enter the reason for the workshop.", [missing]));
// 					return;
// 				}
// 				frappe.call({
// 					method: API + "demobilize_order",
// 					args: { order: frm.doc.name, moves: JSON.stringify(moves) },
// 					freeze: true,
// 				}).then(() => {
// 					d.hide();
// 					frappe.show_alert({ message: __("Status updated"), indicator: "green" });
// 					frm.reload_doc();
// 				});
// 			},
// 		});
// 		d.show();

// 		// reason / workshop boxes only when the new status needs them
// 		d.$wrapper.on("change", "select.dm-goes", function () {
// 			const $r = $(this).closest("tr");
// 			const v = $(this).val();
// 			const changed = v !== $(this).attr("data-current");
// 			$r.find(".dm-reason").prop("disabled", !(changed && (v === "Idle" || v === "Workshop")));
// 			$r.find(".dm-workshop").prop("disabled", !(changed && v === "Workshop"));
// 		});
// 	});
// }


function demobilize(frm) {
	frappe.call({ method: API + "get_order_vehicle_states", args: { order: frm.doc.name } }).then((res) => {
		const rows = res.message || [];
		if (!rows.length) {
			frappe.msgprint(__("This order has no vehicles."));
			return;
		}
		const esc = frappe.utils.escape_html;
		const choices = ["Available", "Idle", "Workshop"];
		const color = { "With Client": "blue", Available: "green", Idle: "orange", Workshop: "red" };
		const today = frappe.datetime.get_today();

		const body = rows
			.map((r) => {
				const opts = (r.state === "With Client" ? [["With Client", __("Stay with client")]] : []).concat(
					choices.map((c) => [c, __(c)])
				);
				const select = `<select class="form-control input-sm dm-goes" data-current="${esc(r.state)}" ${
					r.locked ? "disabled" : ""
				}>${opts
					.map(([v, l]) => `<option value="${v}" ${v === r.state ? "selected" : ""}>${l}</option>`)
					.join("")}</select>`;
				return `<tr data-row="${esc(r.row_name)}">
					<td style="vertical-align:middle"><b>${esc(r.vehicle)}</b></td>
					<td style="vertical-align:middle">${esc(r.driver_name)}</td>
					<td style="vertical-align:middle"><span class="indicator-pill ${color[r.state] || "gray"}">${__(r.state)}</span>${
						r.locked ? `<div class="text-muted small">${__("working on another job")}</div>` : ""
					}</td>
					<td>${select}</td>
					<td><input type="date" class="form-control input-sm dm-from" max="${today}" value="${today}" disabled></td>
					<td><input class="form-control input-sm dm-reason" placeholder="${__("Reason")}" disabled></td>
					<td><input class="form-control input-sm dm-workshop" placeholder="${__("Workshop name")}" disabled></td>
				</tr>`;
			})
			.join("");

		const table = `
			<table class="table table-bordered" style="font-size:13px;">
				<thead><tr>
					<th style="width:11%">${__("Vehicle")}</th>
					<th style="width:15%">${__("Driver")}</th>
					<th style="width:12%">${__("Now")}</th>
					<th style="width:15%">${__("Change to")}</th>
					<th style="width:14%">${__("From Date")} *</th>
					<th style="width:19%">${__("Reason (needed for Workshop)")}</th>
					<th style="width:14%">${__("Workshop")}</th>
				</tr></thead>
				<tbody>${body}</tbody>
			</table>`;

		const d = new frappe.ui.Dialog({
			title: __("Vehicle Status / Demobilize"),
			size: "extra-large",
			fields: [
				{
					fieldtype: "HTML",
					options: `<p class="text-muted">${__(
						"Choose the new status only for the vehicles you want to change. The From Date is when the new status starts; the previous status ends on that date. A vehicle in the workshop must be moved to Idle or Available before it can be used by another customer."
					)}</p>`,
				},
				{
					fieldname: "all",
					label: __("Set all vehicles to"),
					fieldtype: "Select",
					options: "\nAvailable\nIdle\nWorkshop",
					change() {
						const v = d.get_value("all");
						if (!v) return;
						d.$wrapper.find("select.dm-goes:not(:disabled)").each(function () {
							if ($(this).find(`option[value="${v}"]`).length) $(this).val(v).trigger("change");
						});
					},
				},
				{ fieldtype: "HTML", fieldname: "grid", options: table },
			],
			primary_action_label: __("Apply"),
			primary_action() {
				const moves = [];
				let missing = null;       // workshop reason missing
				let missing_date = null;  // from date missing
				let future_date = null;   // from date in the future

				d.$wrapper.find("tr[data-row]").each(function () {
					const $r = $(this);
					const $s = $r.find("select.dm-goes");
					const goes = $s.val();
					if (!goes || goes === $s.attr("data-current")) return; // unchanged row

					const vehicle = $r.find("td:first").text().trim();
					const m = {
						row_name: $r.attr("data-row"),
						goes_to: goes,
						from_date: ($r.find(".dm-from").val() || "").trim(),
						reason: ($r.find(".dm-reason").val() || "").trim(),
						workshop_name: ($r.find(".dm-workshop").val() || "").trim(),
					};
					if (goes === "Workshop" && !m.reason && !missing) missing = vehicle;
					if (!m.from_date && !missing_date) missing_date = vehicle;
					if (m.from_date && m.from_date > today && !future_date) future_date = vehicle;
					moves.push(m);
				});

				if (!moves.length) {
					frappe.msgprint(__("Nothing to change. Every vehicle already has this status."));
					return;
				}
				if (missing_date) {
					frappe.msgprint(__("Vehicle {0}: enter the From Date.", [missing_date]));
					return;
				}
				if (future_date) {
					frappe.msgprint(__("Vehicle {0}: the From Date cannot be in the future.", [future_date]));
					return;
				}
				if (missing) {
					frappe.msgprint(__("Vehicle {0}: enter the reason for the workshop.", [missing]));
					return;
				}
				frappe.call({
					method: API + "demobilize_order",
					args: { order: frm.doc.name, moves: JSON.stringify(moves) },
					freeze: true,
				}).then(() => {
					d.hide();
					frappe.show_alert({ message: __("Status updated"), indicator: "green" });
					frm.reload_doc();
				});
			},
		});
		d.show();

		// From Date is active only for changed rows; reason / workshop only when the new status needs them
		d.$wrapper.on("change", "select.dm-goes", function () {
			const $r = $(this).closest("tr");
			const v = $(this).val();
			const changed = v !== $(this).attr("data-current");
			$r.find(".dm-from").prop("disabled", !changed);
			$r.find(".dm-reason").prop("disabled", !(changed && (v === "Idle" || v === "Workshop")));
			$r.find(".dm-workshop").prop("disabled", !(changed && v === "Workshop"));
		});
	});
}


function swap_assignments(frm) {
	const mine = (frm.doc.vehicles || []).filter((r) => r.status === "Mobilized" && r.deployment);
	if (!mine.length) {
		frappe.msgprint(__("There is no Mobilized row to swap."));
		return;
	}
	const label = (r) => `${r.vehicle}  |  ${r.driver_name || r.driver || ""}`;

	const d = new frappe.ui.Dialog({
		title: __("Swap with Another Site"),
		fields: [
			{
				fieldname: "mode",
				label: __("What to swap"),
				fieldtype: "Select",
				reqd: 1,
				default: "vehicle",
				options: [
					{ label: __("Vehicle only"), value: "vehicle" },
					{ label: __("Driver only"), value: "driver" },
					{ label: __("Vehicle + Driver"), value: "both" },
				],
			},
			{
				fieldname: "row",
				label: __("Row in this order"),
				fieldtype: "Select",
				reqd: 1,
				options: [{ label: "", value: "" }].concat(mine.map((r) => ({ label: label(r), value: r.name }))),
			},
			{
				fieldname: "target_order",
				label: __("Other order (same customer, other site)"),
				fieldtype: "Link",
				options: "Mobilization Order",
				reqd: 1,
				get_query: () => ({
					filters: {
						customer: frm.doc.customer,
						docstatus: 1,
						name: ["!=", frm.doc.name],
						project: ["!=", frm.doc.project],
					},
				}),
				change() {
					const t = d.get_value("target_order");
					if (!t) return;
					frappe.db.get_doc("Mobilization Order", t).then((doc) => {
						const rows = (doc.vehicles || []).filter((r) => r.status === "Mobilized" && r.deployment);
						d.set_df_property(
							"target_row",
							"options",
							[{ label: "", value: "" }].concat(rows.map((r) => ({ label: label(r), value: r.name })))
						);
						d.set_value("target_row", "");
					});
				},
			},
			{
				fieldname: "target_row",
				label: __("Row in the other order"),
				fieldtype: "Select",
				reqd: 1,
			},
			{ fieldname: "reason", label: __("Reason"), fieldtype: "Small Text", reqd: 1 },
		],
		primary_action_label: __("Swap"),
		primary_action(v) {
			frappe.call({
				method: API + "swap_assignments",
				args: {
					order: frm.doc.name,
					row_name: v.row,
					target_order: v.target_order,
					target_row_name: v.target_row,
					mode: v.mode,
					reason: v.reason,
				},
				freeze: true,
				freeze_message: __("Swapping..."),
			}).then(() => {
				d.hide();
				frappe.show_alert({ message: __("Swapped"), indicator: "green" });
				frm.reload_doc();
			});
		},
	});
	d.show();
}