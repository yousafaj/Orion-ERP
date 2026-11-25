frappe.listview_settings["Vehicle Status Log"] = {
	add_fields: ["from_date", "to_date", "status"],
	get_indicator(doc) {
		if (doc.to_date) return [__("Ended"), "gray", "to_date,is,set"];
		return [__("Still {0}", [doc.status]), "orange", "to_date,is,not set"];
	},
	formatters: {
		days(value, df, doc) {
			if (!doc.from_date) return "-";
			const n = frappe.datetime.get_diff(doc.to_date || frappe.datetime.get_today(), doc.from_date);
			return doc.to_date ? n : `<b>${n}</b> <span class="text-muted">(${__("so far")})</span>`;
		},
	},
};