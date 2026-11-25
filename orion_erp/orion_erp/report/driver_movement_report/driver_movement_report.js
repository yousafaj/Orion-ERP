// Driver Movement Report: one row per driver. Click the driver name to see everything in a popup.
// Keep this file in the same folder, with the same file name, as your current Driver Movement Report .js

const DM_API = "orion_erp.orion_erp.validations.fleet_oprations.";

frappe.query_reports["Driver Movement Report"] = {
	filters: [
		{ fieldname: "driver", label: __("Driver (Training Record)"), fieldtype: "Link", options: "Pre-Employment Training" },
		{ fieldname: "driver_name", label: __("Driver Name"), fieldtype: "Data" },
		{ fieldname: "vehicle", label: __("Vehicle"), fieldtype: "Link", options: "Vehicle" },
		{ fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" },
		{
			fieldname: "current_status",
			label: __("Now"),
			fieldtype: "Select",
			options: ["", "On Deployment", "Free"],
		},
		{ fieldname: "from_date", label: __("Mobilized From"), fieldtype: "Date" },
		{ fieldname: "to_date", label: __("Mobilized To"), fieldtype: "Date" },
	],
	formatter(value, row, column, data, default_formatter) {
		if (data && column.fieldname === "driver_name") {
			const id = encodeURIComponent(data.driver_id || "");
			return `<a href="#" onclick="show_driver_history(decodeURIComponent('${id}')); return false;"><b>${frappe.utils.escape_html(
				data.driver_name || "-"
			)}</b></a>`;
		}
		if (data && column.fieldname === "current_status") {
			const color = data.current_status === "On Deployment" ? "green" : "blue";
			return `<span class="indicator-pill ${color}">${__(data.current_status)}</span>`;
		}
		return default_formatter(value, row, column, data);
	},
};

// ======================================================================
// THE POPUP
// ======================================================================

function dmh_inject_style() {
	if (document.getElementById("dmh-style")) return;
	const css = `
	.dmh { color: var(--text-color, #1f272e); }
	.dmh * { box-sizing: border-box; }
	.dmh .muted { color: var(--text-muted, #687178); }

	.dmh-hero { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:14px; }
	.dmh-id { display:flex; align-items:center; gap:14px; }
	.dmh-bigava { width:54px; height:54px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:22px; flex:0 0 auto; }
	.dmh-name { font-size:24px; font-weight:700; line-height:1.1; }
	.dmh-sub { font-size:13px; margin-top:4px; }

	.dmh-pill { display:inline-flex; align-items:center; gap:6px; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600; white-space:nowrap; }
	.dmh-pill:before { content:""; width:7px; height:7px; border-radius:50%; background:currentColor; }
	.dmh-pill.green  { background:var(--bg-green,#e4f5e9);  color:var(--text-on-green,#137949); }
	.dmh-pill.orange { background:var(--bg-orange,#fff1e7); color:var(--text-on-orange,#b4541a); }
	.dmh-pill.gray   { background:var(--bg-gray,#f1f3f4);   color:var(--text-on-gray,#4c5a67); }
	.dmh-pill.blue   { background:var(--bg-blue,#e8f2fd);   color:var(--text-on-blue,#1f6fb5); }
	.dmh-chip { display:inline-block; padding:2px 8px; border-radius:6px; font-size:11.5px; background:var(--control-bg,#f3f3f3); color:var(--text-muted,#687178); }

	.dmh-banner { display:flex; align-items:center; gap:14px; padding:14px 16px; border-radius:12px; margin-bottom:14px; border:1px solid transparent; }
	.dmh-banner.on   { background:var(--bg-green,#e4f5e9); border-color:rgba(19,121,73,.18); }
	.dmh-banner.free { background:var(--bg-blue,#e8f2fd);  border-color:rgba(31,111,181,.18); }
	.dmh-banner .t1 { font-size:15px; font-weight:700; }
	.dmh-banner .t2 { font-size:12.5px; opacity:.85; margin-top:2px; }
	.dmh-ava { flex:0 0 auto; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:16px; }

	.dmh-tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin-bottom:14px; }
	.dmh-tile { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e6e9); border-radius:12px; padding:12px 14px; position:relative; overflow:hidden; }
	.dmh-tile:before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--accent,#2490ef); }
	.dmh-tile .n { font-size:24px; font-weight:700; line-height:1.1; }
	.dmh-tile .l { font-size:12px; margin-top:3px; color:var(--text-muted,#687178); }

	.dmh-card { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e6e9); border-radius:12px; padding:12px 16px; margin-bottom:14px; }
	.dmh-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px 16px; }
	.dmh-kv .k { font-size:11px; text-transform:uppercase; letter-spacing:.4px; color:var(--text-muted,#687178); }
	.dmh-kv .v { font-size:13.5px; font-weight:600; margin-top:2px; word-break:break-word; }

	.dmh-h { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:var(--text-muted,#687178); margin:2px 0 10px; display:flex; align-items:center; gap:8px; }
	.dmh-h:after { content:""; flex:1; height:1px; background:var(--border-color,#e2e6e9); }

	.dmh-tl { position:relative; max-height:46vh; overflow:auto; padding:2px 6px 2px 0; }
	.dmh-item { position:relative; padding-left:34px; padding-bottom:12px; }
	.dmh-item:before { content:""; position:absolute; left:11px; top:22px; bottom:-2px; width:2px; background:var(--border-color,#e2e6e9); }
	.dmh-item:last-child:before { display:none; }
	.dmh-dot { position:absolute; left:3px; top:8px; width:18px; height:18px; border-radius:50%; background:var(--gray-400,#a3acb3); border:3px solid var(--card-bg,#fff); box-shadow:0 0 0 2px var(--gray-300,#d1d8dd); }
	.dmh-item.cur .dmh-dot { background:var(--green-500,#30a66d); box-shadow:0 0 0 2px var(--green-200,#a6e4c3); }
	.dmh-box { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e6e9); border-radius:12px; padding:12px 14px; }
	.dmh-item.cur .dmh-box { border-color:var(--green-300,#7fd2a8); }
	.dmh-row { display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; }
	.dmh-who { display:flex; align-items:center; gap:10px; min-width:0; }
	.dmh-who .ava { width:30px; height:30px; font-size:14px; }
	.dmh-vname { font-weight:700; font-size:14px; }
	.dmh-cust { font-size:12.5px; color:var(--text-muted,#687178); }
	.dmh-meta { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
	.dmh-dates { margin-top:8px; font-size:13px; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
	.dmh-dates b { font-weight:600; }
	.dmh-arrow { color:var(--text-muted,#687178); }
	.dmh-days { font-size:12px; padding:1px 8px; border-radius:6px; background:var(--control-bg,#f3f3f3); }
	.dmh-reason { margin-top:8px; padding:6px 10px; border-left:3px solid var(--orange-400,#f0a05a); background:var(--control-bg,#f6f7f8); border-radius:0 8px 8px 0; font-size:12.5px; }
	.dmh-note { margin-top:8px; padding:6px 10px; border-left:3px solid var(--blue-400,#5aa7f0); background:var(--control-bg,#f6f7f8); border-radius:0 8px 8px 0; font-size:12.5px; }
	.dmh-links { margin-top:8px; font-size:12px; display:flex; gap:14px; flex-wrap:wrap; }
	.dmh-empty { padding:24px; text-align:center; color:var(--text-muted,#687178); }

	@media (max-width: 768px) { .dmh-grid { grid-template-columns:repeat(2,1fr); } }`;
	const el = document.createElement("style");
	el.id = "dmh-style";
	el.textContent = css;
	document.head.appendChild(el);
}

window.show_driver_history = function (driver) {
	dmh_inject_style();
	const d = new frappe.ui.Dialog({
		title: __("Driver History"),
		size: "extra-large",
		fields: [{ fieldtype: "HTML", fieldname: "body" }],
		primary_action_label: __("Open Training Record"),
		primary_action() {
			d.hide();
			frappe.set_route("Form", "Pre-Employment Training", driver);
		},
	});
	d.show();
	d.fields_dict.body.$wrapper.html(`<div class="dmh dmh-empty">${__("Loading...")}</div>`);

	frappe
		.call({ method: DM_API + "get_driver_history", args: { driver: driver } })
		.then((r) => d.fields_dict.body.$wrapper.html(render_driver_history(r.message || {})));
};

function dmh_color(name) {
	let h = 0;
	const s = String(name || "?");
	for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
	return `hsl(${h}, 52%, 44%)`;
}

function render_driver_history(m) {
	const esc = (x) => frappe.utils.escape_html(x == null || x === "" ? "-" : String(x));
	const dt = (x) => (x ? frappe.datetime.str_to_user(x) : "-");
	const initial = (n) => frappe.utils.escape_html(String(n || "?").trim().charAt(0).toUpperCase() || "?");
	const plural = (n, w) => `${n} ${__(w)}${n === 1 ? "" : "s"}`;

	const dr = m.driver || {};
	const s = m.summary || {};
	const cur = m.current;
	const hist = m.history || [];

	// ---------- hero ----------
	const sub = [dr.designation, dr.department].filter(Boolean).map(esc).join(" &nbsp;·&nbsp; ");
	const hero = `
		<div class="dmh-hero">
			<div class="dmh-id">
				<div class="dmh-bigava" style="background:${dmh_color(dr.name)}">${initial(dr.name)}</div>
				<div>
					<div class="dmh-name">${esc(dr.name)}</div>
					<div class="dmh-sub muted">${sub || "&nbsp;"}${dr.employee_id ? ` &nbsp;<span class="dmh-chip">${esc(dr.employee_id)}</span>` : ""}</div>
				</div>
			</div>
			<div>${
				cur
					? `<span class="dmh-pill green">${__("On Deployment")}</span>`
					: `<span class="dmh-pill blue">${__("Free")}</span>`
			}</div>
		</div>`;

	// ---------- now banner ----------
	let banner;
	if (cur) {
		const place = [cur.site, cur.site_location, cur.sub_location].filter(Boolean).map(esc).join(" / ");
		banner = `
		<div class="dmh-banner on">
			<div class="dmh-ava" style="background:var(--green-600,#16905a)">🚛</div>
			<div>
				<div class="t1">${__("Driving vehicle")} <b>${esc(cur.vehicle)}</b> &nbsp;<span style="font-weight:500">${__("at")}</span>&nbsp; ${esc(cur.customer)}</div>
				<div class="t2">${place || "-"} &nbsp;·&nbsp; ${__("since")} ${dt(cur.mobilization_date)} (${plural(cur.days || 1, "day")})</div>
			</div>
		</div>`;
	} else {
		const last = hist[0];
		banner = `
		<div class="dmh-banner free">
			<div class="dmh-ava" style="background:var(--blue-500,#2490ef)">✓</div>
			<div>
				<div class="t1">${__("Free, not deployed at the moment")}</div>
				<div class="t2">${
					last
						? `${__("Last drove vehicle")} <b>${esc(last.vehicle)}</b> ${__("at")} ${esc(last.customer)} ${
								last.actual_end_date ? "· " + __("ended") + " " + dt(last.actual_end_date) : ""
						  }`
						: __("This driver has no deployments yet")
				}</div>
			</div>
		</div>`;
	}

	// ---------- tiles ----------
	const tile = (n, label, accent) =>
		`<div class="dmh-tile" style="--accent:${accent}"><div class="n">${esc(n)}</div><div class="l">${label}</div></div>`;
	const tiles = `
		<div class="dmh-tiles">
			${tile(s.deployments || 0, __("Deployments"), "var(--blue-500,#2490ef)")}
			${tile(s.vehicles || 0, __("Different vehicles"), "var(--purple-500,#7c5cc4)")}
			${tile(s.clients || 0, __("Different clients"), "var(--green-500,#30a66d)")}
			${tile(s.total_days || 0, __("Total days driven"), "var(--orange-500,#e8761b)")}
			${tile(s.times_replaced || 0, __("Times replaced"), "var(--red-500,#e24c4c)")}
		</div>`;

	// ---------- details ----------
	const kv = (k, val) => `<div class="dmh-kv"><div class="k">${k}</div><div class="v">${esc(val)}</div></div>`;
	const details = `
		<div class="dmh-card">
			<div class="dmh-grid">
				${kv(__("Employee ID"), dr.employee_id)}
				${kv(__("Designation"), dr.designation)}
				${kv(__("Department"), dr.department)}
				${kv(__("Company"), dr.company)}
				${kv(__("Employee Status"), dr.status)}
				${kv(__("Mobile"), dr.mobile)}
				${kv(__("Training Records"), dr.training_records)}
			</div>
		</div>`;

	// ---------- timeline ----------
	const link = (dtname, name, label) =>
		name
			? `<a href="/app/${dtname}/${encodeURIComponent(name)}" target="_blank">${label}: <b>${esc(name)}</b></a>`
			: "";

	const items = hist
		.map((h) => {
			const isCur = h.status === "Mobilized";
			const place = [h.site, h.site_location, h.sub_location].filter(Boolean);
			const reasonTag = h.end_reason
				? `<span class="dmh-pill ${/vehicle/i.test(h.end_reason) ? "orange" : /driver/i.test(h.end_reason) ? "blue" : "gray"}">${esc(
						h.end_reason
				  )}</span>`
				: "";

			// what happened next / what came before
			let after = "";
			if (/driver/i.test(h.end_reason || "") && h.next_driver) {
				after = `${__("Replaced by")} <b>${esc(h.next_driver)}</b>`;
			} else if (/vehicle/i.test(h.end_reason || "") && h.next_vehicle) {
				after = `${__("Moved to vehicle")} <b>${esc(h.next_vehicle)}</b>`;
			}
			let before = "";
			if (h.prev_driver && h.prev_driver !== dr.name) {
				before = `${__("Took over from")} <b>${esc(h.prev_driver)}</b>`;
			} else if (h.prev_vehicle && h.prev_vehicle !== h.vehicle) {
				before = `${__("Came from vehicle")} <b>${esc(h.prev_vehicle)}</b>`;
			}
			const notes = [before, after].filter(Boolean).join(" &nbsp;·&nbsp; ");

			return `
			<div class="dmh-item ${isCur ? "cur" : ""}">
				<div class="dmh-dot"></div>
				<div class="dmh-box">
					<div class="dmh-row">
						<div class="dmh-who">
							<div class="dmh-ava ava" style="background:${dmh_color(h.vehicle)}">🚛</div>
							<div>
								<div class="dmh-vname">${esc(h.vehicle)}${h.vehicle_type ? ` <span class="dmh-chip">${esc(h.vehicle_type)}</span>` : ""}</div>
								<div class="dmh-cust">${esc(h.customer)}</div>
							</div>
						</div>
						<div>
							${
								isCur
									? `<span class="dmh-pill green">${__("Mobilized")}</span>`
									: `<span class="dmh-pill gray">${esc(h.status)}</span> ${reasonTag}`
							}
						</div>
					</div>
					${place.length ? `<div class="dmh-meta">${place.map((p) => `<span class="dmh-chip">${esc(p)}</span>`).join("")}</div>` : ""}
					<div class="dmh-dates">
						<b>${dt(h.mobilization_date)}</b>
						<span class="dmh-arrow">→</span>
						<b>${h.actual_end_date ? dt(h.actual_end_date) : __("now")}</b>
						<span class="dmh-days">${h.days != null ? plural(h.days, "day") : "-"}${isCur ? " " + __("so far") : ""}</span>
					</div>
					${notes ? `<div class="dmh-note">${notes}</div>` : ""}
					${h.replacement_reason ? `<div class="dmh-reason"><span class="muted">${__("Reason")}:</span> ${esc(h.replacement_reason)}</div>` : ""}
					<div class="dmh-links">
						${link("vehicle-deployment", h.name, __("Deployment"))}
						${link("mobilization-order", h.mobilization_order, __("Order"))}
					</div>
				</div>
			</div>`;
		})
		.join("");

	const timeline = `
		<div class="dmh-h">${__("Driving history")} (${__("newest first")})</div>
		<div class="dmh-tl">${items || `<div class="dmh-empty">${__("No deployments yet")}</div>`}</div>`;

	return `<div class="dmh">${hero}${banner}${tiles}${details}${timeline}</div>`;
}