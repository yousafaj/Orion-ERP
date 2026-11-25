// // File: apps/orion_erp/orion_erp/orion_erp/report/vehicle_movement_report/vehicle_movement_report.js
// // One row per vehicle. Click the vehicle number to see its full history in a popup.

// const VM_API = "orion_erp.orion_erp.validations.fleet_oprations.";

// frappe.query_reports["Vehicle Movement Report"] = {
// 	filters: [
// 		{ fieldname: "vehicle", label: __("Vehicle"), fieldtype: "Link", options: "Vehicle" },
// 		{ fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" },
// 		{ fieldname: "driver_name", label: __("Driver Name"), fieldtype: "Data" },
// 		{
// 			fieldname: "current_status",
// 			label: __("Now"),
// 			fieldtype: "Select",
// 			options: ["", "On Deployment", "Free"],
// 		},
// 		{ fieldname: "from_date", label: __("Mobilized From"), fieldtype: "Date" },
// 		{ fieldname: "to_date", label: __("Mobilized To"), fieldtype: "Date" },
// 	],
// 	formatter(value, row, column, data, default_formatter) {
// 		if (data && column.fieldname === "vehicle") {
// 			const v = encodeURIComponent(data.vehicle);
// 			return `<a href="#" onclick="show_vehicle_history(decodeURIComponent('${v}')); return false;"><b>${frappe.utils.escape_html(
// 				data.vehicle
// 			)}</b></a>`;
// 		}
// 		if (data && column.fieldname === "current_status") {
// 			const color = data.current_status === "On Deployment" ? "green" : "orange";
// 			return `<span class="indicator-pill ${color}">${__(data.current_status)}</span>`;
// 		}
// 		return default_formatter(value, row, column, data);
// 	},
// };

// // ======================================================================
// // THE POPUP
// // ======================================================================

// function vmh_inject_style() {
// 	if (document.getElementById("vmh-style")) return;
// 	const css = `
// 	.vmh { color: var(--text-color, #1f272e); }
// 	.vmh * { box-sizing: border-box; }
// 	.vmh .muted { color: var(--text-muted, #687178); }

// 	/* hero */
// 	.vmh-hero { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:14px; }
// 	.vmh-plate { font-size:26px; font-weight:700; letter-spacing:.5px; line-height:1.1; }
// 	.vmh-sub { font-size:13px; margin-top:4px; }

// 	/* pills */
// 	.vmh-pill { display:inline-flex; align-items:center; gap:6px; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600; white-space:nowrap; }
// 	.vmh-pill:before { content:""; width:7px; height:7px; border-radius:50%; background:currentColor; }
// 	.vmh-pill.green  { background:var(--bg-green,#e4f5e9);  color:var(--text-on-green,#137949); }
// 	.vmh-pill.orange { background:var(--bg-orange,#fff1e7); color:var(--text-on-orange,#b4541a); }
// 	.vmh-pill.gray   { background:var(--bg-gray,#f1f3f4);   color:var(--text-on-gray,#4c5a67); }
// 	.vmh-pill.blue   { background:var(--bg-blue,#e8f2fd);   color:var(--text-on-blue,#1f6fb5); }
// 	.vmh-pill.red    { background:var(--bg-red,#fdeaea);    color:var(--text-on-red,#b52a2a); }
// 	.vmh-chip { display:inline-block; padding:2px 8px; border-radius:6px; font-size:11.5px; background:var(--control-bg,#f3f3f3); color:var(--text-muted,#687178); }

// 	/* now banner */
// 	.vmh-banner { display:flex; align-items:center; gap:14px; padding:14px 16px; border-radius:12px; margin-bottom:14px; border:1px solid transparent; }
// 	.vmh-banner.on   { background:var(--bg-green,#e4f5e9);  border-color:rgba(19,121,73,.18); }
// 	.vmh-banner.free { background:var(--bg-orange,#fff1e7); border-color:rgba(180,84,26,.18); }
// 	.vmh-banner .t1 { font-size:15px; font-weight:700; }
// 	.vmh-banner .t2 { font-size:12.5px; opacity:.85; margin-top:2px; }
// 	.vmh-ava { flex:0 0 auto; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:16px; }

// 	/* stat tiles */
// 	.vmh-tiles { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:14px; }
// 	.vmh-tile { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e6e9); border-radius:12px; padding:12px 14px; position:relative; overflow:hidden; }
// 	.vmh-tile:before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--accent,#2490ef); }
// 	.vmh-tile .n { font-size:24px; font-weight:700; line-height:1.1; }
// 	.vmh-tile .l { font-size:12px; margin-top:3px; color:var(--text-muted,#687178); }

// 	/* details */
// 	.vmh-card { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e6e9); border-radius:12px; padding:12px 16px; margin-bottom:14px; }
// 	.vmh-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px 16px; }
// 	.vmh-kv .k { font-size:11px; text-transform:uppercase; letter-spacing:.4px; color:var(--text-muted,#687178); }
// 	.vmh-kv .v { font-size:13.5px; font-weight:600; margin-top:2px; word-break:break-word; }

// 	/* section title */
// 	.vmh-h { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:var(--text-muted,#687178); margin:2px 0 10px; display:flex; align-items:center; gap:8px; }
// 	.vmh-h:after { content:""; flex:1; height:1px; background:var(--border-color,#e2e6e9); }

// 	/* timeline */
// 	.vmh-tl { position:relative; max-height:46vh; overflow:auto; padding:2px 6px 2px 0; }
// 	.vmh-item { position:relative; padding-left:34px; padding-bottom:12px; }
// 	.vmh-item:before { content:""; position:absolute; left:11px; top:22px; bottom:-2px; width:2px; background:var(--border-color,#e2e6e9); }
// 	.vmh-item:last-child:before { display:none; }
// 	.vmh-dot { position:absolute; left:3px; top:8px; width:18px; height:18px; border-radius:50%; background:var(--gray-400,#a3acb3); border:3px solid var(--card-bg,#fff); box-shadow:0 0 0 2px var(--gray-300,#d1d8dd); }
// 	.vmh-item.cur .vmh-dot { background:var(--green-500,#30a66d); box-shadow:0 0 0 2px var(--green-200,#a6e4c3); }
// 	.vmh-box { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e6e9); border-radius:12px; padding:12px 14px; }
// 	.vmh-item.cur .vmh-box { border-color:var(--green-300,#7fd2a8); }
// 	.vmh-row { display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; }
// 	.vmh-who { display:flex; align-items:center; gap:10px; min-width:0; }
// 	.vmh-who .ava { width:30px; height:30px; font-size:13px; }
// 	.vmh-name { font-weight:700; font-size:14px; }
// 	.vmh-cust { font-size:12.5px; color:var(--text-muted,#687178); }
// 	.vmh-meta { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
// 	.vmh-dates { margin-top:8px; font-size:13px; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
// 	.vmh-dates b { font-weight:600; }
// 	.vmh-arrow { color:var(--text-muted,#687178); }
// 	.vmh-days { font-size:12px; padding:1px 8px; border-radius:6px; background:var(--control-bg,#f3f3f3); }
// 	.vmh-reason { margin-top:8px; padding:6px 10px; border-left:3px solid var(--orange-400,#f0a05a); background:var(--control-bg,#f6f7f8); border-radius:0 8px 8px 0; font-size:12.5px; }
// 	.vmh-links { margin-top:8px; font-size:12px; display:flex; gap:14px; flex-wrap:wrap; }
// 	.vmh-empty { padding:24px; text-align:center; color:var(--text-muted,#687178); }

// 	@media (max-width: 768px) {
// 		.vmh-tiles, .vmh-grid { grid-template-columns:repeat(2,1fr); }
// 	}`;
// 	const el = document.createElement("style");
// 	el.id = "vmh-style";
// 	el.textContent = css;
// 	document.head.appendChild(el);
// }

// window.show_vehicle_history = function (vehicle) {
// 	vmh_inject_style();
// 	const d = new frappe.ui.Dialog({
// 		title: __("Vehicle History"),
// 		size: "extra-large",
// 		fields: [{ fieldtype: "HTML", fieldname: "body" }],
// 		primary_action_label: __("Open Vehicle"),
// 		primary_action() {
// 			d.hide();
// 			frappe.set_route("Form", "Vehicle", vehicle);
// 		},
// 	});
// 	d.show();
// 	d.fields_dict.body.$wrapper.html(`<div class="vmh vmh-empty">${__("Loading...")}</div>`);

// 	frappe
// 		.call({ method: VM_API + "get_vehicle_history", args: { vehicle: vehicle } })
// 		.then((r) => d.fields_dict.body.$wrapper.html(render_vehicle_history(r.message || {})));
// };

// function vmh_color(name) {
// 	let h = 0;
// 	const s = String(name || "?");
// 	for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
// 	return `hsl(${h}, 52%, 44%)`;
// }

// function render_vehicle_history(m) {
// 	const esc = (x) => frappe.utils.escape_html(x == null || x === "" ? "-" : String(x));
// 	const dt = (x) => (x ? frappe.datetime.str_to_user(x) : "-");
// 	const initial = (n) => frappe.utils.escape_html(String(n || "?").trim().charAt(0).toUpperCase() || "?");
// 	const plural = (n, w) => `${n} ${__(w)}${n === 1 ? "" : "s"}`;

// 	const v = m.vehicle || {};
// 	const s = m.summary || {};
// 	const cur = m.current;
// 	const hist = m.history || [];
// 	const plate = v.name || "";

// 	// ---------- hero ----------
// 	const sub = [v.vehicle_type, v.make].filter(Boolean).map(esc).join(" &nbsp;·&nbsp; ");
// 	const hero = `
// 		<div class="vmh-hero">
// 			<div>
// 				<div class="vmh-plate">${esc(plate)}</div>
// 				<div class="vmh-sub muted">${sub || "&nbsp;"}</div>
// 			</div>
// 			<div>
// 				${
// 					cur
// 						? `<span class="vmh-pill green">${__("On Deployment")}</span>`
// 						: `<span class="vmh-pill orange">${__("Free")}</span>`
// 				}
// 			</div>
// 		</div>`;

// 	// ---------- now banner ----------
// 	let banner;
// 	if (cur) {
// 		const place = [cur.site, cur.site_location, cur.sub_location].filter(Boolean).map(esc).join(" / ");
// 		banner = `
// 		<div class="vmh-banner on">
// 			<div class="vmh-ava" style="background:${vmh_color(cur.driver_name || cur.driver)}">${initial(
// 			cur.driver_name || cur.driver
// 		)}</div>
// 			<div>
// 				<div class="t1">${esc(cur.driver_name || cur.driver)} &nbsp;<span style="font-weight:500">${__("is driving at")}</span>&nbsp; ${esc(cur.customer)}</div>
// 				<div class="t2">${place || "-"} &nbsp;·&nbsp; ${__("since")} ${dt(cur.mobilization_date)} (${plural(cur.days || 1, "day")})</div>
// 			</div>
// 		</div>`;
// 	} else {
// 		const last = hist[0];
// 		banner = `
// 		<div class="vmh-banner free">
// 			<div class="vmh-ava" style="background:var(--orange-500,#e8761b)">!</div>
// 			<div>
// 				<div class="t1">${__("Not deployed at the moment")}</div>
// 				<div class="t2">${
// 					last
// 						? `${__("Last used by")} <b>${esc(last.driver_name || last.driver)}</b> ${__("at")} ${esc(
// 								last.customer
// 						  )} ${last.actual_end_date ? "· " + __("ended") + " " + dt(last.actual_end_date) : ""}`
// 						: __("This vehicle has no deployments yet")
// 				}</div>
// 			</div>
// 		</div>`;
// 	}

// 	// ---------- tiles ----------
// 	const tile = (n, label, accent) =>
// 		`<div class="vmh-tile" style="--accent:${accent}"><div class="n">${esc(n)}</div><div class="l">${label}</div></div>`;
// 	const tiles = `
// 		<div class="vmh-tiles">
// 			${tile(s.deployments || 0, __("Deployments"), "var(--blue-500,#2490ef)")}
// 			${tile(s.drivers || 0, __("Different drivers"), "var(--purple-500,#7c5cc4)")}
// 			${tile(s.clients || 0, __("Different clients"), "var(--green-500,#30a66d)")}
// 			${tile(s.total_days || 0, __("Total days used"), "var(--orange-500,#e8761b)")}
// 		</div>`;

// 	// ---------- details ----------
// 	const kv = (k, val) => `<div class="vmh-kv"><div class="k">${k}</div><div class="v">${esc(val)}</div></div>`;
// 	const details = `
// 		<div class="vmh-card">
// 			<div class="vmh-grid">
// 				${kv(__("Type"), v.vehicle_type)}
// 				${kv(__("Make"), v.make)}
// 				${kv(__("Model"), v.model)}
// 				${kv(__("Chassis No"), v.chassis_no)}
// 				${kv(__("Vehicle Status"), v.status)}
// 				${kv(__("State"), v.state)}
// 				${kv(__("Odometer"), v.odometer)}
// 				${kv(__("Fuel"), v.fuel_type)}
// 			</div>
// 		</div>`;

// 	// ---------- timeline ----------
// 	const link = (dtname, name, label) =>
// 		name
// 			? `<a href="/app/${dtname}/${encodeURIComponent(name)}" target="_blank">${label}: <b>${esc(name)}</b></a>`
// 			: "";

// 	const items = hist
// 		.map((h) => {
// 			const isCur = h.status === "Mobilized";
// 			const who = h.driver_name || h.driver;
// 			const place = [h.site, h.site_location, h.sub_location].filter(Boolean);
// 			const reasonTag = h.end_reason
// 				? `<span class="vmh-pill ${/vehicle/i.test(h.end_reason) ? "orange" : /driver/i.test(h.end_reason) ? "blue" : "gray"}">${esc(
// 						h.end_reason
// 				  )}</span>`
// 				: "";
// 			return `
// 			<div class="vmh-item ${isCur ? "cur" : ""}">
// 				<div class="vmh-dot"></div>
// 				<div class="vmh-box">
// 					<div class="vmh-row">
// 						<div class="vmh-who">
// 							<div class="vmh-ava ava" style="background:${vmh_color(who)}">${initial(who)}</div>
// 							<div>
// 								<div class="vmh-name">${esc(who)}</div>
// 								<div class="vmh-cust">${esc(h.customer)}</div>
// 							</div>
// 						</div>
// 						<div>
// 							${
// 								isCur
// 									? `<span class="vmh-pill green">${__("Mobilized")}</span>`
// 									: `<span class="vmh-pill gray">${esc(h.status)}</span> ${reasonTag}`
// 							}
// 						</div>
// 					</div>
// 					${place.length ? `<div class="vmh-meta">${place.map((p) => `<span class="vmh-chip">${esc(p)}</span>`).join("")}</div>` : ""}
// 					<div class="vmh-dates">
// 						<b>${dt(h.mobilization_date)}</b>
// 						<span class="vmh-arrow">→</span>
// 						<b>${h.actual_end_date ? dt(h.actual_end_date) : __("now")}</b>
// 						<span class="vmh-days">${h.days != null ? plural(h.days, "day") : "-"}${isCur ? " " + __("so far") : ""}</span>
// 					</div>
// 					${h.replacement_reason ? `<div class="vmh-reason"><span class="muted">${__("Reason")}:</span> ${esc(h.replacement_reason)}</div>` : ""}
// 					<div class="vmh-links">
// 						${link("vehicle-deployment", h.name, __("Deployment"))}
// 						${link("mobilization-order", h.mobilization_order, __("Order"))}
// 					</div>
// 				</div>
// 			</div>`;
// 		})
// 		.join("");

// 	const timeline = `
// 		<div class="vmh-h">${__("Movement history")} (${__("newest first")})</div>
// 		<div class="vmh-tl">${items || `<div class="vmh-empty">${__("No deployments yet")}</div>`}</div>`;

// 	return `<div class="vmh">${hero}${banner}${tiles}${details}${timeline}</div>`;
// }



// File: apps/orion_erp/orion_erp/orion_erp/report/vehicle_movement_report/vehicle_movement_report.js
// One row per vehicle. Click the vehicle number to see its full history in a popup
// (deployments + workshop + idle periods).

const VM_API = "orion_erp.orion_erp.validations.fleet_oprations.";

frappe.query_reports["Vehicle Movement Report"] = {
	filters: [
		{ fieldname: "vehicle", label: __("Vehicle"), fieldtype: "Link", options: "Vehicle" },
		{ fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" },
		{ fieldname: "driver_name", label: __("Driver Name"), fieldtype: "Data" },
		{
			fieldname: "current_status",
			label: __("Now"),
			fieldtype: "Select",
			options: ["", "On Deployment", "Workshop", "Idle", "Free"],
		},
		{ fieldname: "from_date", label: __("From Date"), fieldtype: "Date" },
		{ fieldname: "to_date", label: __("To Date"), fieldtype: "Date" },
	],
	formatter(value, row, column, data, default_formatter) {
		if (data && column.fieldname === "vehicle") {
			const v = encodeURIComponent(data.vehicle);
			return `<a href="#" onclick="show_vehicle_history(decodeURIComponent('${v}')); return false;"><b>${frappe.utils.escape_html(
				data.vehicle
			)}</b></a>`;
		}
		if (data && column.fieldname === "current_status") {
			const color = { "On Deployment": "green", Workshop: "red", Idle: "orange", Free: "blue" }[data.current_status] || "gray";
			return `<span class="indicator-pill ${color}">${__(data.current_status)}</span>`;
		}
		return default_formatter(value, row, column, data);
	},
};

// ======================================================================
// THE POPUP
// ======================================================================

function vmh_inject_style() {
	if (document.getElementById("vmh-style")) return;
	const css = `
	.vmh { color: var(--text-color, #1f272e); }
	.vmh * { box-sizing: border-box; }
	.vmh .muted { color: var(--text-muted, #687178); }

	/* hero */
	.vmh-hero { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:14px; }
	.vmh-plate { font-size:26px; font-weight:700; letter-spacing:.5px; line-height:1.1; }
	.vmh-sub { font-size:13px; margin-top:4px; }

	/* pills */
	.vmh-pill { display:inline-flex; align-items:center; gap:6px; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600; white-space:nowrap; }
	.vmh-pill:before { content:""; width:7px; height:7px; border-radius:50%; background:currentColor; }
	.vmh-pill.green  { background:var(--bg-green,#e4f5e9);  color:var(--text-on-green,#137949); }
	.vmh-pill.orange { background:var(--bg-orange,#fff1e7); color:var(--text-on-orange,#b4541a); }
	.vmh-pill.gray   { background:var(--bg-gray,#f1f3f4);   color:var(--text-on-gray,#4c5a67); }
	.vmh-pill.blue   { background:var(--bg-blue,#e8f2fd);   color:var(--text-on-blue,#1f6fb5); }
	.vmh-pill.red    { background:var(--bg-red,#fdeaea);    color:var(--text-on-red,#b52a2a); }
	.vmh-chip { display:inline-block; padding:2px 8px; border-radius:6px; font-size:11.5px; background:var(--control-bg,#f3f3f3); color:var(--text-muted,#687178); }

	/* now banner */
	.vmh-banner { display:flex; align-items:center; gap:14px; padding:14px 16px; border-radius:12px; margin-bottom:14px; border:1px solid transparent; }
	.vmh-banner.on       { background:var(--bg-green,#e4f5e9);  border-color:rgba(19,121,73,.18); }
	.vmh-banner.workshop { background:var(--bg-red,#fdeaea);    border-color:rgba(181,42,42,.18); }
	.vmh-banner.idle     { background:var(--bg-orange,#fff1e7); border-color:rgba(180,84,26,.18); }
	.vmh-banner.free     { background:var(--bg-blue,#e8f2fd);   border-color:rgba(31,111,181,.18); }
	.vmh-banner .t1 { font-size:15px; font-weight:700; }
	.vmh-banner .t2 { font-size:12.5px; opacity:.85; margin-top:2px; }
	.vmh-ava { flex:0 0 auto; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:16px; }

	/* stat tiles */
	.vmh-tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin-bottom:14px; }
	.vmh-tile { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e6e9); border-radius:12px; padding:12px 14px; position:relative; overflow:hidden; }
	.vmh-tile:before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--accent,#2490ef); }
	.vmh-tile .n { font-size:24px; font-weight:700; line-height:1.1; }
	.vmh-tile .l { font-size:12px; margin-top:3px; color:var(--text-muted,#687178); }

	/* details */
	.vmh-card { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e6e9); border-radius:12px; padding:12px 16px; margin-bottom:14px; }
	.vmh-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px 16px; }
	.vmh-kv .k { font-size:11px; text-transform:uppercase; letter-spacing:.4px; color:var(--text-muted,#687178); }
	.vmh-kv .v { font-size:13.5px; font-weight:600; margin-top:2px; word-break:break-word; }

	/* section title */
	.vmh-h { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:var(--text-muted,#687178); margin:2px 0 10px; display:flex; align-items:center; gap:8px; }
	.vmh-h:after { content:""; flex:1; height:1px; background:var(--border-color,#e2e6e9); }

	/* timeline */
	.vmh-tl { position:relative; max-height:46vh; overflow:auto; padding:2px 6px 2px 0; }
	.vmh-item { position:relative; padding-left:34px; padding-bottom:12px; }
	.vmh-item:before { content:""; position:absolute; left:11px; top:22px; bottom:-2px; width:2px; background:var(--border-color,#e2e6e9); }
	.vmh-item:last-child:before { display:none; }
	.vmh-dot { position:absolute; left:3px; top:8px; width:18px; height:18px; border-radius:50%; background:var(--gray-400,#a3acb3); border:3px solid var(--card-bg,#fff); box-shadow:0 0 0 2px var(--gray-300,#d1d8dd); }
	.vmh-item.cur .vmh-dot { background:var(--green-500,#30a66d); box-shadow:0 0 0 2px var(--green-200,#a6e4c3); }
	.vmh-item.ws .vmh-dot   { background:var(--red-500,#e24c4c);    box-shadow:0 0 0 2px var(--red-200,#f5b5b5); }
	.vmh-item.idle .vmh-dot { background:var(--orange-500,#e8761b); box-shadow:0 0 0 2px var(--orange-200,#f8cfa6); }
	.vmh-box { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e6e9); border-radius:12px; padding:12px 14px; }
	.vmh-item.cur .vmh-box { border-color:var(--green-300,#7fd2a8); }
	.vmh-item.ws .vmh-box   { border-left:4px solid var(--red-500,#e24c4c); }
	.vmh-item.idle .vmh-box { border-left:4px solid var(--orange-500,#e8761b); }
	.vmh-row { display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; }
	.vmh-who { display:flex; align-items:center; gap:10px; min-width:0; }
	.vmh-who .ava { width:30px; height:30px; font-size:13px; }
	.vmh-name { font-weight:700; font-size:14px; }
	.vmh-cust { font-size:12.5px; color:var(--text-muted,#687178); }
	.vmh-meta { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
	.vmh-dates { margin-top:8px; font-size:13px; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
	.vmh-dates b { font-weight:600; }
	.vmh-arrow { color:var(--text-muted,#687178); }
	.vmh-days { font-size:12px; padding:1px 8px; border-radius:6px; background:var(--control-bg,#f3f3f3); }
	.vmh-reason { margin-top:8px; padding:6px 10px; border-left:3px solid var(--orange-400,#f0a05a); background:var(--control-bg,#f6f7f8); border-radius:0 8px 8px 0; font-size:12.5px; }
	.vmh-links { margin-top:8px; font-size:12px; display:flex; gap:14px; flex-wrap:wrap; }
	.vmh-empty { padding:24px; text-align:center; color:var(--text-muted,#687178); }

	@media (max-width: 768px) {
		.vmh-grid { grid-template-columns:repeat(2,1fr); }
	}`;
	const el = document.createElement("style");
	el.id = "vmh-style";
	el.textContent = css;
	document.head.appendChild(el);
}

window.show_vehicle_history = function (vehicle) {
	vmh_inject_style();
	const d = new frappe.ui.Dialog({
		title: __("Vehicle History"),
		size: "extra-large",
		fields: [{ fieldtype: "HTML", fieldname: "body" }],
		primary_action_label: __("Open Vehicle"),
		primary_action() {
			d.hide();
			frappe.set_route("Form", "Vehicle", vehicle);
		},
	});
	d.show();
	d.fields_dict.body.$wrapper.html(`<div class="vmh vmh-empty">${__("Loading...")}</div>`);

	frappe
		.call({ method: VM_API + "get_vehicle_history", args: { vehicle: vehicle } })
		.then((r) => d.fields_dict.body.$wrapper.html(render_vehicle_history(r.message || {})));
};

function vmh_color(name) {
	let h = 0;
	const s = String(name || "?");
	for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
	return `hsl(${h}, 52%, 44%)`;
}

function render_vehicle_history(m) {
	const esc = (x) => frappe.utils.escape_html(x == null || x === "" ? "-" : String(x));
	const dt = (x) => (x ? frappe.datetime.str_to_user(x) : "-");
	const initial = (n) => frappe.utils.escape_html(String(n || "?").trim().charAt(0).toUpperCase() || "?");
	const plural = (n, w) => `${n} ${__(w)}${n === 1 ? "" : "s"}`;

	const v = m.vehicle || {};
	const s = m.summary || {};
	const cur = m.current;
	const now = m.now || { kind: cur ? "On Deployment" : "Free" };
	const hist = m.history || [];
	const plate = v.name || "";

	const pillColor = { "On Deployment": "green", Workshop: "red", Idle: "orange", Free: "blue" };
	const nowLabel = { "On Deployment": __("On Deployment"), Workshop: __("In Workshop"), Idle: __("Idle"), Free: __("Free") };

	// ---------- hero ----------
	const sub = [v.vehicle_type, v.make].filter(Boolean).map(esc).join(" &nbsp;·&nbsp; ");
	const hero = `
		<div class="vmh-hero">
			<div>
				<div class="vmh-plate">${esc(plate)}</div>
				<div class="vmh-sub muted">${sub || "&nbsp;"}</div>
			</div>
			<div><span class="vmh-pill ${pillColor[now.kind] || "gray"}">${nowLabel[now.kind] || esc(now.kind)}</span></div>
		</div>`;

	// ---------- now banner ----------
	const lastDeployment = hist.find((h) => (h.kind || "deployment") === "deployment");
	let banner;
	if (now.kind === "On Deployment" && cur) {
		const place = [cur.site, cur.site_location, cur.sub_location].filter(Boolean).map(esc).join(" / ");
		banner = `
		<div class="vmh-banner on">
			<div class="vmh-ava" style="background:${vmh_color(cur.driver_name || cur.driver)}">${initial(cur.driver_name || cur.driver)}</div>
			<div>
				<div class="t1">${esc(cur.driver_name || cur.driver)} &nbsp;<span style="font-weight:500">${__("is driving at")}</span>&nbsp; ${esc(cur.customer)}</div>
				<div class="t2">${place || "-"} &nbsp;·&nbsp; ${__("since")} ${dt(cur.mobilization_date)} (${plural(cur.days || 1, "day")})</div>
			</div>
		</div>`;
	} else if (now.kind === "Workshop" || now.kind === "Idle") {
		const isW = now.kind === "Workshop";
		const detail = [now.workshop_name, now.reason].filter(Boolean).map(esc).join(" &nbsp;·&nbsp; ");
		banner = `
		<div class="vmh-banner ${isW ? "workshop" : "idle"}">
			<div class="vmh-ava" style="background:${isW ? "var(--red-500,#e24c4c)" : "var(--orange-500,#e8761b)"}">${isW ? "🔧" : "⏸"}</div>
			<div>
				<div class="t1">${isW ? __("In the workshop") : __("Idle, waiting for the next job")} &nbsp;<span style="font-weight:500">${__("since")} ${dt(now.since)} (${plural(now.days || 1, "day")})</span></div>
				<div class="t2">${detail || (isW ? __("No details entered") : __("No job assigned"))}</div>
			</div>
		</div>`;
	} else {
		banner = `
		<div class="vmh-banner free">
			<div class="vmh-ava" style="background:var(--blue-500,#2490ef)">✓</div>
			<div>
				<div class="t1">${__("Available, not deployed at the moment")}</div>
				<div class="t2">${
					lastDeployment
						? `${__("Last used by")} <b>${esc(lastDeployment.driver_name || lastDeployment.driver)}</b> ${__("at")} ${esc(
								lastDeployment.customer
						  )} ${lastDeployment.actual_end_date ? "· " + __("ended") + " " + dt(lastDeployment.actual_end_date) : ""}`
						: __("This vehicle has no deployments yet")
				}</div>
			</div>
		</div>`;
	}

	// ---------- tiles ----------
	const tile = (n, label, accent) =>
		`<div class="vmh-tile" style="--accent:${accent}"><div class="n">${esc(n)}</div><div class="l">${label}</div></div>`;
	const tiles = `
		<div class="vmh-tiles">
			${tile(s.deployments || 0, __("Deployments"), "var(--blue-500,#2490ef)")}
			${tile(s.drivers || 0, __("Different drivers"), "var(--purple-500,#7c5cc4)")}
			${tile(s.clients || 0, __("Different clients"), "var(--green-500,#30a66d)")}
			${tile(s.total_days || 0, __("Days on deployment"), "var(--cyan-500,#1aa9b8)")}
			${tile(s.workshop_days || 0, `${__("Days in workshop")} (${s.workshop_times || 0}×)`, "var(--red-500,#e24c4c)")}
			${tile(s.idle_days || 0, __("Days idle"), "var(--orange-500,#e8761b)")}
		</div>`;

	// ---------- details ----------
	const kv = (k, val) => `<div class="vmh-kv"><div class="k">${k}</div><div class="v">${esc(val)}</div></div>`;
	const details = `
		<div class="vmh-card">
			<div class="vmh-grid">
				${kv(__("Type"), v.vehicle_type)}
				${kv(__("Make"), v.make)}
				${kv(__("Model"), v.model)}
				${kv(__("Chassis No"), v.chassis_no)}
				${kv(__("Vehicle Status"), v.status)}
				${kv(__("State"), v.state)}
				${kv(__("Odometer"), v.odometer)}
				${kv(__("Fuel"), v.fuel_type)}
			</div>
		</div>`;

	// ---------- timeline ----------
	const link = (dtname, name, label) =>
		name
			? `<a href="/app/${dtname}/${encodeURIComponent(name)}" target="_blank">${label}: <b>${esc(name)}</b></a>`
			: "";

	const items = hist
		.map((h) => {
			const kind = h.kind || "deployment";

			// ----- workshop / idle period -----
			if (kind === "Workshop" || kind === "Idle") {
				const isW = kind === "Workshop";
				const open = !h.to_date;
				return `
				<div class="vmh-item ${isW ? "ws" : "idle"}">
					<div class="vmh-dot"></div>
					<div class="vmh-box">
						<div class="vmh-row">
							<div class="vmh-who">
								<div class="vmh-ava ava" style="background:${isW ? "var(--red-500,#e24c4c)" : "var(--orange-500,#e8761b)"}">${isW ? "🔧" : "⏸"}</div>
								<div>
									<div class="vmh-name">${isW ? __("In Workshop") : __("Idle")}</div>
									<div class="vmh-cust">${h.workshop_name ? esc(h.workshop_name) : "&nbsp;"}</div>
								</div>
							</div>
							<div><span class="vmh-pill ${open ? (isW ? "red" : "orange") : "gray"}">${open ? __("Ongoing") : __("Ended")}</span></div>
						</div>
						<div class="vmh-dates">
							<b>${dt(h.from_date)}</b>
							<span class="vmh-arrow">→</span>
							<b>${h.to_date ? dt(h.to_date) : __("now")}</b>
							<span class="vmh-days">${h.days != null ? plural(h.days, "day") : "-"}${open ? " " + __("so far") : ""}</span>
						</div>
						${h.reason ? `<div class="vmh-reason"><span class="muted">${__("Reason")}:</span> ${esc(h.reason)}</div>` : ""}
						<div class="vmh-links">${link("mobilization-order", h.source_order, __("After order"))}</div>
					</div>
				</div>`;
			}

			// ----- deployment -----
			const isCur = h.status === "Mobilized";
			const who = h.driver_name || h.driver;
			const place = [h.site, h.site_location, h.sub_location].filter(Boolean);
			const reasonTag = h.end_reason
				? `<span class="vmh-pill ${/vehicle/i.test(h.end_reason) ? "orange" : /driver/i.test(h.end_reason) ? "blue" : "gray"}">${esc(
						h.end_reason
				  )}</span>`
				: "";
			return `
			<div class="vmh-item ${isCur ? "cur" : ""}">
				<div class="vmh-dot"></div>
				<div class="vmh-box">
					<div class="vmh-row">
						<div class="vmh-who">
							<div class="vmh-ava ava" style="background:${vmh_color(who)}">${initial(who)}</div>
							<div>
								<div class="vmh-name">${esc(who)}</div>
								<div class="vmh-cust">${esc(h.customer)}</div>
							</div>
						</div>
						<div>
							${
								isCur
									? `<span class="vmh-pill green">${__("Mobilized")}</span>`
									: `<span class="vmh-pill gray">${esc(h.status)}</span> ${reasonTag}`
							}
						</div>
					</div>
					${place.length ? `<div class="vmh-meta">${place.map((p) => `<span class="vmh-chip">${esc(p)}</span>`).join("")}</div>` : ""}
					<div class="vmh-dates">
						<b>${dt(h.mobilization_date)}</b>
						<span class="vmh-arrow">→</span>
						<b>${h.actual_end_date ? dt(h.actual_end_date) : __("now")}</b>
						<span class="vmh-days">${h.days != null ? plural(h.days, "day") : "-"}${isCur ? " " + __("so far") : ""}</span>
					</div>
					${h.replacement_reason ? `<div class="vmh-reason"><span class="muted">${__("Reason")}:</span> ${esc(h.replacement_reason)}</div>` : ""}
					<div class="vmh-links">
						${link("vehicle-deployment", h.name, __("Deployment"))}
						${link("mobilization-order", h.mobilization_order, __("Order"))}
					</div>
				</div>
			</div>`;
		})
		.join("");

	const timeline = `
		<div class="vmh-h">${__("Movement history")} (${__("newest first")})</div>
		<div class="vmh-tl">${items || `<div class="vmh-empty">${__("No history yet")}</div>`}</div>`;

	return `<div class="vmh">${hero}${banner}${tiles}${details}${timeline}</div>`;
}