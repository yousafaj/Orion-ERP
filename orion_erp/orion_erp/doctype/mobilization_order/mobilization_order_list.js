frappe.listview_settings["Mobilization Order"] = {
	onload(listview) {
		// remove the broken style from the previous version
		$("#mo-list-style").remove();

		const add_vehicle_filter = () => {
        const $section = listview.page.page_form.find(".standard-filter-section").first();
        if (!$section.length) return false;

        listview.page.page_form.find(".vehicle-filter-box").remove();

        // sits BEFORE the section, on the same line as the other filters
        const $box = $(`<div class="form-group frappe-control vehicle-filter-box"
            style="flex:0 0 130px;width:130px;min-width:130px;margin:0 8px 0 0;"></div>`);
        $section.before($box);

        $("#mo-list-style").remove();
        $("head").append(`<style id="mo-list-style">
            .page-form { flex-wrap: nowrap !important; align-items: center; }
            .page-form .standard-filter-section { flex-wrap: nowrap !important; }
            .page-form .standard-filter-section .form-group { flex: 0 0 120px !important; width: 120px !important; min-width: 120px !important; margin-bottom: 0 !important; }
        </style>`);

        const control = frappe.ui.form.make_control({
            df: { fieldtype: "Link", fieldname: "vehicle_search", options: "Vehicle", placeholder: __("Vehicle") },
            parent: $box,
            render_input: true,
        });

        const apply = (value) => {
            listview.filter_area.filter_list.filters
                .filter((f) => f.doctype === "Mobilization Order Vehicle" && f.fieldname === "vehicle")
                .forEach((f) => f.remove());
            if (value) {
                listview.filter_area.add([["Mobilization Order Vehicle", "vehicle", "=", value]]);
            } else {
                listview.refresh();
            }
        };
        control.df.change = () => apply(control.get_value());
        control.$input && control.$input.on("awesomplete-selectcomplete", () => apply(control.get_value()));
        return true;
    };
		// the standard filters may not be drawn yet, so retry briefly
		if (!add_vehicle_filter()) {
			let tries = 0;
			const t = setInterval(() => {
				if (add_vehicle_filter() || ++tries > 20) clearInterval(t);
			}, 150);
		}
	},


		refresh(listview) {
		const COL = "flex:0 0 330px;max-width:330px;white-space:nowrap;overflow:hidden;";
		const ORDER = ["With Client", "Pending", "Idle", "Workshop", "Demobilized"];
		const color = {
			"With Client": "blue", Pending: "yellow", Idle: "orange",
			Workshop: "red", Demobilized: "gray",
		};

		listview.$result.find(".vs-col").remove();
		listview.$result
			.find(".list-row-head .level-left")
			.append(`<div class="list-row-col hidden-xs vs-col" style="${COL}"><span>${__("Vehicle Status")}</span></div>`);

		const names = (listview.data || []).map((d) => d.name);
		if (!names.length) return;

		const show_details = (order, vehicles) => {
			const esc = frappe.utils.escape_html;
			const rows = vehicles
				.map(
					(v) => `<tr>
						<td><b>${esc(v.vehicle)}</b></td>
						<td><span class="indicator-pill ${color[v.state] || "gray"}">${__(v.state)}</span></td>
					</tr>`
				)
				.join("");
			const d = new frappe.ui.Dialog({
				title: __("{0}: vehicle status", [order]),
				fields: [
					{ fieldname: "q", fieldtype: "Data", label: __("Search vehicle") },
					{
						fieldtype: "HTML",
						options: `<div style="max-height:400px;overflow:auto;">
							<table class="table table-bordered" style="font-size:13px;">
								<thead><tr><th>${__("Vehicle")}</th><th>${__("Status")}</th></tr></thead>
								<tbody class="vs-rows">${rows}</tbody>
							</table></div>`,
					},
				],
			});
			d.show();
			d.fields_dict.q.$input.on("input", function () {
				const q = ($(this).val() || "").toLowerCase();
				d.$wrapper.find(".vs-rows tr").each(function () {
					$(this).toggle($(this).text().toLowerCase().includes(q));
				});
			});
		};

		frappe.call({
			method: "orion_erp.orion_erp.validations.fleet_oprations.get_orders_vehicle_states",
			args: { orders: JSON.stringify(names) },
		}).then((r) => {
			const data = r.message || {};
			listview.$result.find(".list-row-container").each(function () {
				const $c = $(this);
				const name = $c.find(".list-subject a").attr("data-name");
				if (!name) return;
				$c.find(".vs-col").remove();

				const vehicles = data[name] || [];
				const counts = {};
				vehicles.forEach((v) => (counts[v.state] = (counts[v.state] || 0) + 1));

				const pills = ORDER.filter((s) => counts[s])
					.map((s) => `<span class="indicator-pill ${color[s]}" style="margin-right:4px;">${counts[s]} ${__(s)}</span>`)
					.join("");

				const $cell = $(
					`<div class="list-row-col hidden-xs vs-col" style="${COL}cursor:pointer;" title="${__("Click to see all vehicles")}">${pills || "-"}</div>`
				);
				$cell.on("click", (e) => {
					e.stopPropagation();
					e.preventDefault();
					show_details(name, vehicles);
				});
				$c.find(".list-row .level-left").append($cell);
			});
		});
	},
};




