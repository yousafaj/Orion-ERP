# # Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.utils import flt, cint


# def execute(filters=None):
# 	filters = filters or {}

# 	if filters.get("drilldown_type") and filters.get("drilldown_vehicle"):
# 		return get_drilldown(filters)

# 	if not filters.get("from_date") or not filters.get("to_date"):
# 		return get_columns(filters), []

# 	consolidated = cint(filters.get("consolidated"))
# 	company = filters.get("company")

# 	if not consolidated and not company:
# 		frappe.msgprint(
# 			frappe._("Please select a Company or enable Consolidated mode.")
# 		)
# 		return get_columns(filters), []

# 	columns = get_columns(filters)
# 	data = get_data(filters, consolidated)
# 	return columns, data


# # ------------------------------------------------------------------
# # Columns
# # ------------------------------------------------------------------

# def get_columns(filters):
# 	consolidated = cint(filters.get("consolidated")) if filters else 0
# 	cols = []

# 	if consolidated:
# 		cols.append({
# 			"label": "Company",
# 			"fieldname": "company",
# 			"fieldtype": "Link",
# 			"options": "Company",
# 			"width": 150
# 		})

# 	cols.extend([
# 		{
# 			"label": "Vehicle No",
# 			"fieldname": "vehicle",
# 			"fieldtype": "Link",
# 			"options": "Vehicle",
# 			"width": 180
# 		},
# 		{
# 			"label": "Sales Amount",
# 			"fieldname": "sales_amount",
# 			"fieldtype": "Currency",
# 			"width": 150
# 		},
# 		{
# 			"label": "Purchase Amount",
# 			"fieldname": "purchase_amount",
# 			"fieldtype": "Currency",
# 			"width": 150
# 		},
# 		{
# 			"label": "JV Debit Amount",
# 			"fieldname": "jv_debit_amount",
# 			"fieldtype": "Currency",
# 			"width": 150
# 		},
# 		{
# 			"label": "JV Credit Amount",
# 			"fieldname": "jv_credit_amount",
# 			"fieldtype": "Currency",
# 			"width": 150
# 		},
# 		{
# 			"label": "Gross Profit",
# 			"fieldname": "gross_profit",
# 			"fieldtype": "Currency",
# 			"width": 150
# 		}
# 	])
# 	return cols


# # ------------------------------------------------------------------
# # Main data dispatcher
# # ------------------------------------------------------------------

# def get_data(filters, consolidated):
# 	if consolidated:
# 		return _get_consolidated_data(filters)
# 	return _get_single_company_data(filters)


# # ------------------------------------------------------------------
# # Single-company mode (original behaviour, company now optional)
# # ------------------------------------------------------------------

# def _get_single_company_data(filters):
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")
# 	company = filters.get("company")
# 	cost_center = filters.get("cost_center")
# 	vehicle = filters.get("vehicle")

# 	# --- Sales subquery ---
# 	sales_params = [from_date, to_date, company]
# 	sales_cc = ""
# 	if cost_center:
# 		sales_cc = " AND sii.cost_center = %s"
# 		sales_params.append(cost_center)

# 	sales_subquery = f"""
# 		SELECT
# 			sii.vehicle_details,
# 			SUM(sii.amount) AS sales_amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si
# 			ON si.name = sii.parent
# 		WHERE si.docstatus = 1
# 		  AND si.posting_date BETWEEN %s AND %s
# 		  AND si.company = %s
# 		  {sales_cc}
# 		GROUP BY sii.vehicle_details
# 	"""

# 	# --- Purchase subquery ---
# 	purchase_params = [from_date, to_date, company]
# 	purchase_cc = ""
# 	if cost_center:
# 		purchase_cc = " AND pii.cost_center = %s"
# 		purchase_params.append(cost_center)

# 	purchase_subquery = f"""
# 		SELECT
# 			pii.vehicle_details,
# 			SUM(pii.amount) AS purchase_amount
# 		FROM `tabPurchase Invoice Item` pii
# 		INNER JOIN `tabPurchase Invoice` pi
# 			ON pi.name = pii.parent
# 		WHERE pi.docstatus = 1
# 		  AND pi.posting_date BETWEEN %s AND %s
# 		  AND pi.company = %s
# 		  {purchase_cc}
# 		GROUP BY pii.vehicle_details
# 	"""

# 	# --- Journal Entry subquery ---
# 	jv_params = [from_date, to_date, company]
# 	jv_cc = ""
# 	if cost_center:
# 		jv_cc = " AND jea.cost_center = %s"
# 		jv_params.append(cost_center)

# 	jv_subquery = f"""
# 		SELECT
# 			jea.vehicle_details,
# 			SUM(CASE WHEN jea.debit > 0 THEN jea.debit ELSE 0 END) AS jv_debit_amount,
# 			SUM(CASE WHEN jea.credit > 0 THEN jea.credit ELSE 0 END) AS jv_credit_amount
# 		FROM `tabJournal Entry Account` jea
# 		INNER JOIN `tabJournal Entry` je
# 			ON je.name = jea.parent
# 		WHERE je.docstatus = 1
# 		  AND je.posting_date BETWEEN %s AND %s
# 		  AND je.company = %s
# 		  {jv_cc}
# 		GROUP BY jea.vehicle_details
# 	"""

# 	# --- Vehicle filter ---
# 	vehicle_filter = ""
# 	vehicle_params = []
# 	if vehicle:
# 		vehicle_filter = " AND v.name = %s"
# 		vehicle_params = [vehicle]

# 	all_params = sales_params + purchase_params + jv_params + vehicle_params

# 	query = f"""
# 		SELECT
# 			v.name AS vehicle,
# 			COALESCE(s.sales_amount, 0) AS sales_amount,
# 			COALESCE(p.purchase_amount, 0) AS purchase_amount,
# 			COALESCE(j.jv_debit_amount, 0) AS jv_debit_amount,
# 			COALESCE(j.jv_credit_amount, 0) AS jv_credit_amount,
# 			(
# 				COALESCE(s.sales_amount, 0)
# 				- COALESCE(p.purchase_amount, 0)
# 				- COALESCE(j.jv_debit_amount, 0)
# 				+ COALESCE(j.jv_credit_amount, 0)
# 			) AS gross_profit
# 		FROM `tabVehicle` v
# 		LEFT JOIN ({sales_subquery}) s
# 			ON s.vehicle_details = v.name
# 		LEFT JOIN ({purchase_subquery}) p
# 			ON p.vehicle_details = v.name
# 		LEFT JOIN ({jv_subquery}) j
# 			ON j.vehicle_details = v.name
# 		WHERE 1=1
# 		{vehicle_filter}
# 		ORDER BY v.name
# 	"""

# 	return frappe.db.sql(query, tuple(all_params), as_dict=True)


# # ------------------------------------------------------------------
# # Consolidated mode – fetch from all companies, merge in Python
# # ------------------------------------------------------------------

# def _get_consolidated_data(filters):
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")
# 	cost_center = filters.get("cost_center")
# 	vehicle = filters.get("vehicle")

# 	base_params = [from_date, to_date]

# 	# --- Sales ---
# 	sales_cc = ""
# 	sales_cc_params = []
# 	if cost_center:
# 		sales_cc = " AND sii.cost_center = %s"
# 		sales_cc_params = [cost_center]

# 	sales_v = ""
# 	sales_v_params = []
# 	if vehicle:
# 		sales_v = " AND sii.vehicle_details = %s"
# 		sales_v_params = [vehicle]

# 	sales = frappe.db.sql(f"""
# 		SELECT
# 			si.company,
# 			sii.vehicle_details AS vehicle,
# 			SUM(sii.amount) AS sales_amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si
# 			ON si.name = sii.parent
# 		WHERE si.docstatus = 1
# 		  AND si.posting_date BETWEEN %s AND %s
# 		  {sales_cc}
# 		  {sales_v}
# 		GROUP BY si.company, sii.vehicle_details
# 	""", tuple(base_params + sales_cc_params + sales_v_params), as_dict=True)

# 	# --- Purchase ---
# 	purchase_cc = ""
# 	purchase_cc_params = []
# 	if cost_center:
# 		purchase_cc = " AND pii.cost_center = %s"
# 		purchase_cc_params = [cost_center]

# 	purchase_v = ""
# 	purchase_v_params = []
# 	if vehicle:
# 		purchase_v = " AND pii.vehicle_details = %s"
# 		purchase_v_params = [vehicle]

# 	purchases = frappe.db.sql(f"""
# 		SELECT
# 			pi.company,
# 			pii.vehicle_details AS vehicle,
# 			SUM(pii.amount) AS purchase_amount
# 		FROM `tabPurchase Invoice Item` pii
# 		INNER JOIN `tabPurchase Invoice` pi
# 			ON pi.name = pii.parent
# 		WHERE pi.docstatus = 1
# 		  AND pi.posting_date BETWEEN %s AND %s
# 		  {purchase_cc}
# 		  {purchase_v}
# 		GROUP BY pi.company, pii.vehicle_details
# 	""", tuple(base_params + purchase_cc_params + purchase_v_params), as_dict=True)

# 	# --- Journal Entries ---
# 	jv_cc = ""
# 	jv_cc_params = []
# 	if cost_center:
# 		jv_cc = " AND jea.cost_center = %s"
# 		jv_cc_params = [cost_center]

# 	jv_v = ""
# 	jv_v_params = []
# 	if vehicle:
# 		jv_v = " AND jea.vehicle_details = %s"
# 		jv_v_params = [vehicle]

# 	jvs = frappe.db.sql(f"""
# 		SELECT
# 			je.company,
# 			jea.vehicle_details AS vehicle,
# 			SUM(CASE WHEN jea.debit > 0 THEN jea.debit ELSE 0 END) AS jv_debit_amount,
# 			SUM(CASE WHEN jea.credit > 0 THEN jea.credit ELSE 0 END) AS jv_credit_amount
# 		FROM `tabJournal Entry Account` jea
# 		INNER JOIN `tabJournal Entry` je
# 			ON je.name = jea.parent
# 		WHERE je.docstatus = 1
# 		  AND je.posting_date BETWEEN %s AND %s
# 		  {jv_cc}
# 		  {jv_v}
# 		GROUP BY je.company, jea.vehicle_details
# 	""", tuple(base_params + jv_cc_params + jv_v_params), as_dict=True)

# 	# --- Merge by (vehicle, company) ---
# 	_empty = {
# 		"sales_amount": 0, "purchase_amount": 0,
# 		"jv_debit_amount": 0, "jv_credit_amount": 0
# 	}

# 	merged = {}
# 	for row in sales:
# 		if not row.vehicle:
# 			continue
# 		key = (row.vehicle, row.company)
# 		merged.setdefault(key, {"vehicle": row.vehicle, "company": row.company, **_empty})
# 		merged[key]["sales_amount"] = flt(row.sales_amount)

# 	for row in purchases:
# 		if not row.vehicle:
# 			continue
# 		key = (row.vehicle, row.company)
# 		merged.setdefault(key, {"vehicle": row.vehicle, "company": row.company, **_empty})
# 		merged[key]["purchase_amount"] = flt(row.purchase_amount)

# 	for row in jvs:
# 		if not row.vehicle:
# 			continue
# 		key = (row.vehicle, row.company)
# 		merged.setdefault(key, {"vehicle": row.vehicle, "company": row.company, **_empty})
# 		merged[key]["jv_debit_amount"] = flt(row.jv_debit_amount)
# 		merged[key]["jv_credit_amount"] = flt(row.jv_credit_amount)

# 	frappe.logger().info(
# 		f"Vehicle GP Consolidated: sales={len(sales)}, purchases={len(purchases)}, "
# 		f"jvs={len(jvs)}, merged={len(merged)}"
# 	)

# 	data = []
# 	for key in sorted(merged, key=lambda x: (str(x[0] or ""), str(x[1] or ""))):
# 		row = merged[key]
# 		row["gross_profit"] = (
# 			row["sales_amount"]
# 			- row["purchase_amount"]
# 			- row["jv_debit_amount"]
# 			+ row["jv_credit_amount"]
# 		)
# 		data.append(row)

# 	if not data:
# 		frappe.msgprint(
# 			frappe._("No data found for the selected filters. "
# 					 "Please verify that transactions have a Vehicle assigned.")
# 		)

# 	return data


# # ==================================================================
# # Drill-down helpers
# # ==================================================================

# def _drilldown_conditions(vehicle, from_date, to_date, company, cost_center,
# 						   doc_alias, item_alias):
# 	"""Build WHERE fragment and params for a detail drill-down query."""
# 	conditions = (
# 		f"AND {item_alias}.vehicle_details = %s "
# 		f"AND {doc_alias}.posting_date BETWEEN %s AND %s"
# 	)
# 	params = [vehicle, from_date, to_date]

# 	if company:
# 		conditions += f" AND {doc_alias}.company = %s"
# 		params.append(company)

# 	if cost_center:
# 		conditions += f" AND {item_alias}.cost_center = %s"
# 		params.append(cost_center)

# 	return conditions, params


# def get_drilldown(filters):
# 	drilldown_type = filters.get("drilldown_type")
# 	vehicle = filters.get("drilldown_vehicle")
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")
# 	consolidated = cint(filters.get("consolidated"))
# 	company = filters.get("drilldown_company") if consolidated else filters.get("company")
# 	cost_center = filters.get("cost_center")

# 	if drilldown_type == "sales_amount":
# 		columns, data = _get_sales_drilldown(vehicle, from_date, to_date, company, cost_center)
# 	elif drilldown_type == "purchase_amount":
# 		columns, data = _get_purchase_drilldown(vehicle, from_date, to_date, company, cost_center)
# 	elif drilldown_type == "jv_debit_amount":
# 		columns, data = _get_jv_drilldown(vehicle, from_date, to_date, company, cost_center, "debit")
# 	elif drilldown_type == "jv_credit_amount":
# 		columns, data = _get_jv_drilldown(vehicle, from_date, to_date, company, cost_center, "credit")
# 	elif drilldown_type == "gross_profit":
# 		columns, data = _get_gp_drilldown(vehicle, from_date, to_date, company, cost_center)
# 	else:
# 		return [], []

# 	# Tuple return: (columns, data, message, chart, report_summary, skip_total_row)
# 	# skip_total_row=True suppresses the Report JSON's add_total_row
# 	return columns, data, None, None, None, True


# # ------------------------------------------------------------------
# # Sales drill-down
# # ------------------------------------------------------------------

# def _get_sales_drilldown(vehicle, from_date, to_date, company, cost_center):
# 	cond, params = _drilldown_conditions(
# 		vehicle, from_date, to_date, company, cost_center,
# 		doc_alias="si", item_alias="sii"
# 	)

# 	columns = [
# 		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
# 		{"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link",
# 		 "options": "Sales Invoice", "width": 180},
# 		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 180},
# 		{"label": "Item", "fieldname": "item", "fieldtype": "Data", "width": 200},
# 		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
# 	]

# 	data = frappe.db.sql(f"""
# 		SELECT
# 			si.posting_date,
# 			si.name AS sales_invoice,
# 			si.customer_name AS customer,
# 			sii.item_name AS item,
# 			sii.amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si
# 			ON si.name = sii.parent
# 		WHERE si.docstatus = 1
# 		  {cond}
# 		ORDER BY si.posting_date
# 	""", tuple(params), as_dict=True)

# 	return columns, data


# # ------------------------------------------------------------------
# # Purchase drill-down
# # ------------------------------------------------------------------

# def _get_purchase_drilldown(vehicle, from_date, to_date, company, cost_center):
# 	cond, params = _drilldown_conditions(
# 		vehicle, from_date, to_date, company, cost_center,
# 		doc_alias="pi", item_alias="pii"
# 	)

# 	columns = [
# 		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
# 		{"label": "Purchase Invoice", "fieldname": "purchase_invoice", "fieldtype": "Link",
# 		 "options": "Purchase Invoice", "width": 180},
# 		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 180},
# 		{"label": "Item", "fieldname": "item", "fieldtype": "Data", "width": 200},
# 		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
# 	]

# 	data = frappe.db.sql(f"""
# 		SELECT
# 			pi.posting_date,
# 			pi.name AS purchase_invoice,
# 			pi.supplier_name AS supplier,
# 			pii.item_name AS item,
# 			pii.amount
# 		FROM `tabPurchase Invoice Item` pii
# 		INNER JOIN `tabPurchase Invoice` pi
# 			ON pi.name = pii.parent
# 		WHERE pi.docstatus = 1
# 		  {cond}
# 		ORDER BY pi.posting_date
# 	""", tuple(params), as_dict=True)

# 	return columns, data


# # ------------------------------------------------------------------
# # Journal Entry drill-down (debit or credit)
# # ------------------------------------------------------------------

# def _get_jv_drilldown(vehicle, from_date, to_date, company, cost_center, mode):
# 	conditions = (
# 		"AND jea.vehicle_details = %s "
# 		"AND je.posting_date BETWEEN %s AND %s"
# 	)
# 	params = [vehicle, from_date, to_date]

# 	if company:
# 		conditions += " AND je.company = %s"
# 		params.append(company)

# 	if cost_center:
# 		conditions += " AND jea.cost_center = %s"
# 		params.append(cost_center)

# 	if mode == "debit":
# 		conditions += " AND jea.debit > 0"
# 		amount_expr = "jea.debit"
# 		label = "Debit"
# 	else:
# 		conditions += " AND jea.credit > 0"
# 		amount_expr = "jea.credit"
# 		label = "Credit"

# 	columns = [
# 		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
# 		{"label": "Journal Entry", "fieldname": "journal_entry", "fieldtype": "Link",
# 		 "options": "Journal Entry", "width": 180},
# 		{"label": "Account", "fieldname": "account", "fieldtype": "Link",
# 		 "options": "Account", "width": 200},
# 		{"label": label, "fieldname": "amount", "fieldtype": "Currency", "width": 150},
# 		{"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data", "width": 250},
# 	]

# 	data = frappe.db.sql(f"""
# 		SELECT
# 			je.posting_date,
# 			je.name AS journal_entry,
# 			jea.account,
# 			{amount_expr} AS amount,
# 			je.remark AS remarks
# 		FROM `tabJournal Entry Account` jea
# 		INNER JOIN `tabJournal Entry` je
# 			ON je.name = jea.parent
# 		WHERE je.docstatus = 1
# 		  {conditions}
# 		ORDER BY je.posting_date
# 	""", tuple(params), as_dict=True)

# 	return columns, data


# # ------------------------------------------------------------------
# # Gross Profit drill-down (all transactions for the vehicle)
# # ------------------------------------------------------------------

# def _get_gp_drilldown(vehicle, from_date, to_date, company, cost_center):
# 	columns = [
# 		{"label": "Tran No", "fieldname": "docname", "fieldtype": "Dynamic Link",
# 		 "options": "link_doctype", "width": 180},
# 		{"label": "Type", "fieldname": "tran_type", "fieldtype": "Data", "width": 140},
# 		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
# 		{"label": "Party / Account", "fieldname": "party", "fieldtype": "Data", "width": 200},
# 		{"label": "Details", "fieldname": "details", "fieldtype": "Data", "width": 200},
# 		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
# 	]

# 	data = []

# 	# --- Sales ---
# 	sales_cond, sales_params = _drilldown_conditions(
# 		vehicle, from_date, to_date, company, cost_center,
# 		doc_alias="si", item_alias="sii"
# 	)

# 	sales = frappe.db.sql(f"""
# 		SELECT si.name AS docname, si.posting_date, si.customer_name AS party,
# 		       sii.item_name AS details, sii.amount, si.is_return
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# 		WHERE si.docstatus = 1 {sales_cond}
# 		ORDER BY si.posting_date
# 	""", tuple(sales_params), as_dict=True)

# 	for s in sales:
# 		amount = -abs(flt(s.amount)) if s.is_return else abs(flt(s.amount))
# 		data.append({
# 			"docname": s.docname,
# 			"link_doctype": "Sales Invoice",
# 			"tran_type": "Sales Credit Note" if s.is_return else "Sales Invoice",
# 			"posting_date": s.posting_date,
# 			"party": s.party,
# 			"details": s.details,
# 			"amount": amount,
# 		})

# 	# --- Purchase ---
# 	purchase_cond, purchase_params = _drilldown_conditions(
# 		vehicle, from_date, to_date, company, cost_center,
# 		doc_alias="pi", item_alias="pii"
# 	)

# 	purchases = frappe.db.sql(f"""
# 		SELECT pi.name AS docname, pi.posting_date, pi.supplier_name AS party,
# 		       pii.item_name AS details, pii.amount, pi.is_return
# 		FROM `tabPurchase Invoice Item` pii
# 		INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
# 		WHERE pi.docstatus = 1 {purchase_cond}
# 		ORDER BY pi.posting_date
# 	""", tuple(purchase_params), as_dict=True)

# 	for p in purchases:
# 		amount = -abs(flt(p.amount)) if p.is_return else abs(flt(p.amount))
# 		data.append({
# 			"docname": p.docname,
# 			"link_doctype": "Purchase Invoice",
# 			"tran_type": "Purchase Credit Note" if p.is_return else "Purchase Invoice",
# 			"posting_date": p.posting_date,
# 			"party": p.party,
# 			"details": p.details,
# 			"amount": amount,
# 		})

# 	# --- Journal Entries ---
# 	jv_conditions = (
# 		"AND jea.vehicle_details = %s "
# 		"AND je.posting_date BETWEEN %s AND %s"
# 	)
# 	jv_params = [vehicle, from_date, to_date]
# 	if company:
# 		jv_conditions += " AND je.company = %s"
# 		jv_params.append(company)
# 	if cost_center:
# 		jv_conditions += " AND jea.cost_center = %s"
# 		jv_params.append(cost_center)

# 	jvs = frappe.db.sql(f"""
# 		SELECT je.name AS docname, je.posting_date, jea.account AS party,
# 		       je.remark AS details,
# 		       jea.debit AS debit, jea.credit AS credit
# 		FROM `tabJournal Entry Account` jea
# 		INNER JOIN `tabJournal Entry` je ON je.name = jea.parent
# 		WHERE je.docstatus = 1 {jv_conditions}
# 		ORDER BY je.posting_date
# 	""", tuple(jv_params), as_dict=True)

# 	for j in jvs:
# 		debit = flt(j.debit)
# 		credit = flt(j.credit)

# 		if debit > 0 and credit <= 0:
# 			tran_type = "Journal Debit"
# 			amount = debit
# 		elif credit > 0 and debit <= 0:
# 			tran_type = "Journal Credit"
# 			amount = -credit
# 		elif debit > credit:
# 			tran_type = "Journal Debit"
# 			amount = debit - credit
# 		elif credit > debit:
# 			tran_type = "Journal Credit"
# 			amount = -(credit - debit)
# 		else:
# 			tran_type = "Journal Entry"
# 			amount = 0

# 		data.append({
# 			"docname": j.docname,
# 			"link_doctype": "Journal Entry",
# 			"tran_type": tran_type,
# 			"posting_date": j.posting_date,
# 			"party": j.party,
# 			"details": j.details,
# 			"amount": amount,
# 		})

# 	# Sort detail rows by date
# 	detail_rows = [d for d in data if d.get("posting_date")]
# 	detail_rows.sort(key=lambda x: str(x.get("posting_date")))

# 	# Calculate totals
# 	total_sales = sum(
# 		d["amount"] for d in detail_rows
# 		if d.get("link_doctype") == "Sales Invoice"
# 	)
# 	total_purchase = sum(
# 		d["amount"] for d in detail_rows
# 		if d.get("link_doctype") == "Purchase Invoice"
# 	)
# 	total_jv = sum(
# 		d["amount"] for d in detail_rows
# 		if d.get("link_doctype") == "Journal Entry"
# 	)

# 	_summary_base = {
# 		"docname": None, "link_doctype": None, "tran_type": None,
# 		"posting_date": None, "party": None, "details": None,
# 	}

# 	# Append summary rows after detail rows
# 	detail_rows.append({**_summary_base, "amount": None})
# 	detail_rows.append({**_summary_base, "tran_type": "Total Sales", "amount": flt(total_sales)})
# 	detail_rows.append({**_summary_base, "tran_type": "Total Purchase", "amount": flt(total_purchase)})
# 	detail_rows.append({**_summary_base, "tran_type": "Total Journal Entries", "amount": flt(total_jv)})
# 	detail_rows.append({
# 		**_summary_base,
# 		"tran_type": "Gross Profit",
# 		"amount": flt(total_sales - total_purchase - total_jv),
# 	})

# 	return columns, detail_rows



import frappe
from frappe.utils import flt, cint


def execute(filters=None):
	filters = filters or {}

	if filters.get("drilldown_type") and filters.get("drilldown_vehicle"):
		return get_drilldown(filters)

	if not filters.get("from_date") or not filters.get("to_date"):
		return get_columns(filters), []

	consolidated = cint(filters.get("consolidated"))
	company = filters.get("company")

	if not consolidated and not company:
		frappe.msgprint(
			frappe._("Please select a Company or enable Consolidated mode.")
		)
		return get_columns(filters), []

	columns = get_columns(filters)
	data = get_data(filters, consolidated)
	return columns, data


# ------------------------------------------------------------------
# Columns
# ------------------------------------------------------------------

def get_columns(filters):
	consolidated = cint(filters.get("consolidated")) if filters else 0
	cols = []

	# Consolidated mode: one row per vehicle (all companies together), so no Company column
	cols.extend([
		{
			"label": "Vehicle No",
			"fieldname": "vehicle",
			"fieldtype": "Link",
			"options": "Vehicle",
			"width": 180
		},
		{
			"label": "Sales Amount",
			"fieldname": "sales_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": "Purchase Amount",
			"fieldname": "purchase_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": "JV Debit Amount",
			"fieldname": "jv_debit_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": "JV Credit Amount",
			"fieldname": "jv_credit_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": "Gross Profit",
			"fieldname": "gross_profit",
			"fieldtype": "Currency",
			"width": 150
		}
	])
	return cols


# ------------------------------------------------------------------
# Main data dispatcher
# ------------------------------------------------------------------

def get_data(filters, consolidated):
	if consolidated:
		return _get_consolidated_data(filters)
	return _get_single_company_data(filters)


# ------------------------------------------------------------------
# Single-company mode (original behaviour, company now optional)
# ------------------------------------------------------------------

def _get_single_company_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	company = filters.get("company")
	cost_center = filters.get("cost_center")
	vehicle = filters.get("vehicle")

	# --- Sales subquery ---
	sales_params = [from_date, to_date, company]
	sales_cc = ""
	if cost_center:
		sales_cc = " AND sii.cost_center = %s"
		sales_params.append(cost_center)

	sales_subquery = f"""
		SELECT
			sii.vehicle_details,
			SUM(sii.amount) AS sales_amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si
			ON si.name = sii.parent
		WHERE si.docstatus = 1
		  AND si.posting_date BETWEEN %s AND %s
		  AND si.company = %s
		  {sales_cc}
		GROUP BY sii.vehicle_details
	"""

	# --- Purchase subquery ---
	purchase_params = [from_date, to_date, company]
	purchase_cc = ""
	if cost_center:
		purchase_cc = " AND pii.cost_center = %s"
		purchase_params.append(cost_center)

	purchase_subquery = f"""
		SELECT
			pii.vehicle_details,
			SUM(pii.amount) AS purchase_amount
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi
			ON pi.name = pii.parent
		WHERE pi.docstatus = 1
		  AND pi.posting_date BETWEEN %s AND %s
		  AND pi.company = %s
		  {purchase_cc}
		GROUP BY pii.vehicle_details
	"""

	# --- Journal Entry subquery ---
	jv_params = [from_date, to_date, company]
	jv_cc = ""
	if cost_center:
		jv_cc = " AND jea.cost_center = %s"
		jv_params.append(cost_center)

	jv_subquery = f"""
		SELECT
			jea.vehicle_details,
			SUM(CASE WHEN jea.debit > 0 THEN jea.debit ELSE 0 END) AS jv_debit_amount,
			SUM(CASE WHEN jea.credit > 0 THEN jea.credit ELSE 0 END) AS jv_credit_amount
		FROM `tabJournal Entry Account` jea
		INNER JOIN `tabJournal Entry` je
			ON je.name = jea.parent
		WHERE je.docstatus = 1
		  AND je.posting_date BETWEEN %s AND %s
		  AND je.company = %s
		  {jv_cc}
		GROUP BY jea.vehicle_details
	"""

	# --- Vehicle filter ---
	vehicle_filter = ""
	vehicle_params = []
	if vehicle:
		vehicle_filter = " AND v.name = %s"
		vehicle_params = [vehicle]

	all_params = sales_params + purchase_params + jv_params + vehicle_params

	query = f"""
		SELECT
			v.name AS vehicle,
			COALESCE(s.sales_amount, 0) AS sales_amount,
			COALESCE(p.purchase_amount, 0) AS purchase_amount,
			COALESCE(j.jv_debit_amount, 0) AS jv_debit_amount,
			COALESCE(j.jv_credit_amount, 0) AS jv_credit_amount,
			(
				COALESCE(s.sales_amount, 0)
				- COALESCE(p.purchase_amount, 0)
				- COALESCE(j.jv_debit_amount, 0)
				+ COALESCE(j.jv_credit_amount, 0)
			) AS gross_profit
		FROM `tabVehicle` v
		LEFT JOIN ({sales_subquery}) s
			ON s.vehicle_details = v.name
		LEFT JOIN ({purchase_subquery}) p
			ON p.vehicle_details = v.name
		LEFT JOIN ({jv_subquery}) j
			ON j.vehicle_details = v.name
		WHERE 1=1
		{vehicle_filter}
		ORDER BY v.name
	"""

	return frappe.db.sql(query, tuple(all_params), as_dict=True)


# ------------------------------------------------------------------
# Consolidated mode – fetch from all companies, merge in Python
# ------------------------------------------------------------------

def _get_consolidated_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	cost_center = filters.get("cost_center")
	vehicle = filters.get("vehicle")

	base_params = [from_date, to_date]

	# --- Sales ---
	sales_cc = ""
	sales_cc_params = []
	if cost_center:
		sales_cc = " AND sii.cost_center = %s"
		sales_cc_params = [cost_center]

	sales_v = ""
	sales_v_params = []
	if vehicle:
		sales_v = " AND sii.vehicle_details = %s"
		sales_v_params = [vehicle]

	sales = frappe.db.sql(f"""
		SELECT
			sii.vehicle_details AS vehicle,
			SUM(sii.amount) AS sales_amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si
			ON si.name = sii.parent
		WHERE si.docstatus = 1
		  AND si.posting_date BETWEEN %s AND %s
		  {sales_cc}
		  {sales_v}
		GROUP BY sii.vehicle_details
	""", tuple(base_params + sales_cc_params + sales_v_params), as_dict=True)

	# --- Purchase ---
	purchase_cc = ""
	purchase_cc_params = []
	if cost_center:
		purchase_cc = " AND pii.cost_center = %s"
		purchase_cc_params = [cost_center]

	purchase_v = ""
	purchase_v_params = []
	if vehicle:
		purchase_v = " AND pii.vehicle_details = %s"
		purchase_v_params = [vehicle]

	purchases = frappe.db.sql(f"""
		SELECT
			pii.vehicle_details AS vehicle,
			SUM(pii.amount) AS purchase_amount
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi
			ON pi.name = pii.parent
		WHERE pi.docstatus = 1
		  AND pi.posting_date BETWEEN %s AND %s
		  {purchase_cc}
		  {purchase_v}
		GROUP BY pii.vehicle_details
	""", tuple(base_params + purchase_cc_params + purchase_v_params), as_dict=True)

	# --- Journal Entries ---
	jv_cc = ""
	jv_cc_params = []
	if cost_center:
		jv_cc = " AND jea.cost_center = %s"
		jv_cc_params = [cost_center]

	jv_v = ""
	jv_v_params = []
	if vehicle:
		jv_v = " AND jea.vehicle_details = %s"
		jv_v_params = [vehicle]

	jvs = frappe.db.sql(f"""
		SELECT
			jea.vehicle_details AS vehicle,
			SUM(CASE WHEN jea.debit > 0 THEN jea.debit ELSE 0 END) AS jv_debit_amount,
			SUM(CASE WHEN jea.credit > 0 THEN jea.credit ELSE 0 END) AS jv_credit_amount
		FROM `tabJournal Entry Account` jea
		INNER JOIN `tabJournal Entry` je
			ON je.name = jea.parent
		WHERE je.docstatus = 1
		  AND je.posting_date BETWEEN %s AND %s
		  {jv_cc}
		  {jv_v}
		GROUP BY jea.vehicle_details
	""", tuple(base_params + jv_cc_params + jv_v_params), as_dict=True)

	# --- Merge by vehicle (all companies together) ---
	_empty = {
		"sales_amount": 0, "purchase_amount": 0,
		"jv_debit_amount": 0, "jv_credit_amount": 0
	}

	merged = {}
	for row in sales:
		if not row.vehicle:
			continue
		key = row.vehicle
		merged.setdefault(key, {"vehicle": row.vehicle, **_empty})
		merged[key]["sales_amount"] = flt(row.sales_amount)

	for row in purchases:
		if not row.vehicle:
			continue
		key = row.vehicle
		merged.setdefault(key, {"vehicle": row.vehicle, **_empty})
		merged[key]["purchase_amount"] = flt(row.purchase_amount)

	for row in jvs:
		if not row.vehicle:
			continue
		key = row.vehicle
		merged.setdefault(key, {"vehicle": row.vehicle, **_empty})
		merged[key]["jv_debit_amount"] = flt(row.jv_debit_amount)
		merged[key]["jv_credit_amount"] = flt(row.jv_credit_amount)

	frappe.logger().info(
		f"Vehicle GP Consolidated: sales={len(sales)}, purchases={len(purchases)}, "
		f"jvs={len(jvs)}, merged={len(merged)}"
	)

	data = []
	for key in sorted(merged, key=lambda x: str(x or "")):
		row = merged[key]
		row["gross_profit"] = (
			row["sales_amount"]
			- row["purchase_amount"]
			- row["jv_debit_amount"]
			+ row["jv_credit_amount"]
		)
		data.append(row)

	if not data:
		frappe.msgprint(
			frappe._("No data found for the selected filters. "
					 "Please verify that transactions have a Vehicle assigned.")
		)

	return data


# ==================================================================
# Drill-down helpers
# ==================================================================

def _drilldown_conditions(vehicle, from_date, to_date, company, cost_center,
						   doc_alias, item_alias):
	"""Build WHERE fragment and params for a detail drill-down query."""
	conditions = (
		f"AND {item_alias}.vehicle_details = %s "
		f"AND {doc_alias}.posting_date BETWEEN %s AND %s"
	)
	params = [vehicle, from_date, to_date]

	if company:
		conditions += f" AND {doc_alias}.company = %s"
		params.append(company)

	if cost_center:
		conditions += f" AND {item_alias}.cost_center = %s"
		params.append(cost_center)

	return conditions, params


def get_drilldown(filters):
	drilldown_type = filters.get("drilldown_type")
	vehicle = filters.get("drilldown_vehicle")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	consolidated = cint(filters.get("consolidated"))
	company = filters.get("drilldown_company") if consolidated else filters.get("company")
	cost_center = filters.get("cost_center")

	if drilldown_type == "sales_amount":
		columns, data = _get_sales_drilldown(vehicle, from_date, to_date, company, cost_center)
	elif drilldown_type == "purchase_amount":
		columns, data = _get_purchase_drilldown(vehicle, from_date, to_date, company, cost_center)
	elif drilldown_type == "jv_debit_amount":
		columns, data = _get_jv_drilldown(vehicle, from_date, to_date, company, cost_center, "debit")
	elif drilldown_type == "jv_credit_amount":
		columns, data = _get_jv_drilldown(vehicle, from_date, to_date, company, cost_center, "credit")
	elif drilldown_type == "gross_profit":
		columns, data = _get_gp_drilldown(vehicle, from_date, to_date, company, cost_center)
	else:
		return [], []

	# Tuple return: (columns, data, message, chart, report_summary, skip_total_row)
	# skip_total_row=True suppresses the Report JSON's add_total_row
	return columns, data, None, None, None, True


# ------------------------------------------------------------------
# Sales drill-down
# ------------------------------------------------------------------

def _get_sales_drilldown(vehicle, from_date, to_date, company, cost_center):
	cond, params = _drilldown_conditions(
		vehicle, from_date, to_date, company, cost_center,
		doc_alias="si", item_alias="sii"
	)

	columns = [
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link",
		 "options": "Sales Invoice", "width": 180},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 180},
		{"label": "Item", "fieldname": "item", "fieldtype": "Data", "width": 200},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
	]

	data = frappe.db.sql(f"""
		SELECT
			si.posting_date,
			si.name AS sales_invoice,
			si.customer_name AS customer,
			sii.item_name AS item,
			sii.amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si
			ON si.name = sii.parent
		WHERE si.docstatus = 1
		  {cond}
		ORDER BY si.posting_date
	""", tuple(params), as_dict=True)

	return columns, data


# ------------------------------------------------------------------
# Purchase drill-down
# ------------------------------------------------------------------

def _get_purchase_drilldown(vehicle, from_date, to_date, company, cost_center):
	cond, params = _drilldown_conditions(
		vehicle, from_date, to_date, company, cost_center,
		doc_alias="pi", item_alias="pii"
	)

	columns = [
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{"label": "Purchase Invoice", "fieldname": "purchase_invoice", "fieldtype": "Link",
		 "options": "Purchase Invoice", "width": 180},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 180},
		{"label": "Item", "fieldname": "item", "fieldtype": "Data", "width": 200},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
	]

	data = frappe.db.sql(f"""
		SELECT
			pi.posting_date,
			pi.name AS purchase_invoice,
			pi.supplier_name AS supplier,
			pii.item_name AS item,
			pii.amount
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi
			ON pi.name = pii.parent
		WHERE pi.docstatus = 1
		  {cond}
		ORDER BY pi.posting_date
	""", tuple(params), as_dict=True)

	return columns, data


# ------------------------------------------------------------------
# Journal Entry drill-down (debit or credit)
# ------------------------------------------------------------------

def _get_jv_drilldown(vehicle, from_date, to_date, company, cost_center, mode):
	conditions = (
		"AND jea.vehicle_details = %s "
		"AND je.posting_date BETWEEN %s AND %s"
	)
	params = [vehicle, from_date, to_date]

	if company:
		conditions += " AND je.company = %s"
		params.append(company)

	if cost_center:
		conditions += " AND jea.cost_center = %s"
		params.append(cost_center)

	if mode == "debit":
		conditions += " AND jea.debit > 0"
		amount_expr = "jea.debit"
		label = "Debit"
	else:
		conditions += " AND jea.credit > 0"
		amount_expr = "jea.credit"
		label = "Credit"

	columns = [
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{"label": "Journal Entry", "fieldname": "journal_entry", "fieldtype": "Link",
		 "options": "Journal Entry", "width": 180},
		{"label": "Account", "fieldname": "account", "fieldtype": "Link",
		 "options": "Account", "width": 200},
		{"label": label, "fieldname": "amount", "fieldtype": "Currency", "width": 150},
		{"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data", "width": 250},
	]

	data = frappe.db.sql(f"""
		SELECT
			je.posting_date,
			je.name AS journal_entry,
			jea.account,
			{amount_expr} AS amount,
			je.remark AS remarks
		FROM `tabJournal Entry Account` jea
		INNER JOIN `tabJournal Entry` je
			ON je.name = jea.parent
		WHERE je.docstatus = 1
		  {conditions}
		ORDER BY je.posting_date
	""", tuple(params), as_dict=True)

	return columns, data


# ------------------------------------------------------------------
# Gross Profit drill-down (all transactions for the vehicle)
# (kept for backward compatibility; the Gross Profit column now opens
#  the popup statement via get_vehicle_statement below)
# ------------------------------------------------------------------

def _get_gp_drilldown(vehicle, from_date, to_date, company, cost_center):
	columns = [
		{"label": "Tran No", "fieldname": "docname", "fieldtype": "Dynamic Link",
		 "options": "link_doctype", "width": 180},
		{"label": "Type", "fieldname": "tran_type", "fieldtype": "Data", "width": 140},
		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{"label": "Party / Account", "fieldname": "party", "fieldtype": "Data", "width": 200},
		{"label": "Details", "fieldname": "details", "fieldtype": "Data", "width": 200},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
	]

	data = []

	# --- Sales ---
	sales_cond, sales_params = _drilldown_conditions(
		vehicle, from_date, to_date, company, cost_center,
		doc_alias="si", item_alias="sii"
	)

	sales = frappe.db.sql(f"""
		SELECT si.name AS docname, si.posting_date, si.customer_name AS party,
		       sii.item_name AS details, sii.amount, si.is_return
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 {sales_cond}
		ORDER BY si.posting_date
	""", tuple(sales_params), as_dict=True)

	for s in sales:
		amount = -abs(flt(s.amount)) if s.is_return else abs(flt(s.amount))
		data.append({
			"docname": s.docname,
			"link_doctype": "Sales Invoice",
			"tran_type": "Sales Credit Note" if s.is_return else "Sales Invoice",
			"posting_date": s.posting_date,
			"party": s.party,
			"details": s.details,
			"amount": amount,
		})

	# --- Purchase ---
	purchase_cond, purchase_params = _drilldown_conditions(
		vehicle, from_date, to_date, company, cost_center,
		doc_alias="pi", item_alias="pii"
	)

	purchases = frappe.db.sql(f"""
		SELECT pi.name AS docname, pi.posting_date, pi.supplier_name AS party,
		       pii.item_name AS details, pii.amount, pi.is_return
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		WHERE pi.docstatus = 1 {purchase_cond}
		ORDER BY pi.posting_date
	""", tuple(purchase_params), as_dict=True)

	for p in purchases:
		amount = -abs(flt(p.amount)) if p.is_return else abs(flt(p.amount))
		data.append({
			"docname": p.docname,
			"link_doctype": "Purchase Invoice",
			"tran_type": "Purchase Credit Note" if p.is_return else "Purchase Invoice",
			"posting_date": p.posting_date,
			"party": p.party,
			"details": p.details,
			"amount": amount,
		})

	# --- Journal Entries ---
	jv_conditions = (
		"AND jea.vehicle_details = %s "
		"AND je.posting_date BETWEEN %s AND %s"
	)
	jv_params = [vehicle, from_date, to_date]
	if company:
		jv_conditions += " AND je.company = %s"
		jv_params.append(company)
	if cost_center:
		jv_conditions += " AND jea.cost_center = %s"
		jv_params.append(cost_center)

	jvs = frappe.db.sql(f"""
		SELECT je.name AS docname, je.posting_date, jea.account AS party,
		       je.remark AS details,
		       jea.debit AS debit, jea.credit AS credit
		FROM `tabJournal Entry Account` jea
		INNER JOIN `tabJournal Entry` je ON je.name = jea.parent
		WHERE je.docstatus = 1 {jv_conditions}
		ORDER BY je.posting_date
	""", tuple(jv_params), as_dict=True)

	for j in jvs:
		debit = flt(j.debit)
		credit = flt(j.credit)

		if debit > 0 and credit <= 0:
			tran_type = "Journal Debit"
			amount = debit
		elif credit > 0 and debit <= 0:
			tran_type = "Journal Credit"
			amount = -credit
		elif debit > credit:
			tran_type = "Journal Debit"
			amount = debit - credit
		elif credit > debit:
			tran_type = "Journal Credit"
			amount = -(credit - debit)
		else:
			tran_type = "Journal Entry"
			amount = 0

		data.append({
			"docname": j.docname,
			"link_doctype": "Journal Entry",
			"tran_type": tran_type,
			"posting_date": j.posting_date,
			"party": j.party,
			"details": j.details,
			"amount": amount,
		})

	# Sort detail rows by date
	detail_rows = [d for d in data if d.get("posting_date")]
	detail_rows.sort(key=lambda x: str(x.get("posting_date")))

	# Calculate totals
	total_sales = sum(
		d["amount"] for d in detail_rows
		if d.get("link_doctype") == "Sales Invoice"
	)
	total_purchase = sum(
		d["amount"] for d in detail_rows
		if d.get("link_doctype") == "Purchase Invoice"
	)
	total_jv = sum(
		d["amount"] for d in detail_rows
		if d.get("link_doctype") == "Journal Entry"
	)

	_summary_base = {
		"docname": None, "link_doctype": None, "tran_type": None,
		"posting_date": None, "party": None, "details": None,
	}

	# Append summary rows after detail rows
	detail_rows.append({**_summary_base, "amount": None})
	detail_rows.append({**_summary_base, "tran_type": "Total Sales", "amount": flt(total_sales)})
	detail_rows.append({**_summary_base, "tran_type": "Total Purchase", "amount": flt(total_purchase)})
	detail_rows.append({**_summary_base, "tran_type": "Total Journal Entries", "amount": flt(total_jv)})
	detail_rows.append({
		**_summary_base,
		"tran_type": "Gross Profit",
		"amount": flt(total_sales - total_purchase - total_jv),
	})

	return columns, detail_rows


# ==================================================================
# Popup statement (Gross Profit click) – layout like the Excel sheet
# ==================================================================

@frappe.whitelist()
def get_vehicle_statement(vehicle, from_date, to_date, company=None, cost_center=None):
	"""Return the data for the Gross Profit popup (statement layout)."""

	def _where(doc, item):
		return _drilldown_conditions(
			vehicle, from_date, to_date, company, cost_center,
			doc_alias=doc, item_alias=item
		)

	# --- Sales ---
	cond, params = _where("si", "sii")
	sales = frappe.db.sql(f"""
		SELECT si.company, si.name AS ref, si.posting_date AS date,
		       si.customer_name AS party, sii.item_name AS details, sii.amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 {cond}
		ORDER BY si.posting_date
	""", tuple(params), as_dict=True)

	# --- Purchase ---
	cond, params = _where("pi", "pii")
	purchases = frappe.db.sql(f"""
		SELECT pi.company, pi.name AS ref, pi.posting_date AS date,
		       pi.supplier_name AS party, pii.item_name AS details, pii.amount
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		WHERE pi.docstatus = 1 {cond}
		ORDER BY pi.posting_date
	""", tuple(params), as_dict=True)

	# --- Journal Entries ---
	jv_cond = "AND jea.vehicle_details = %s AND je.posting_date BETWEEN %s AND %s"
	jv_params = [vehicle, from_date, to_date]
	if company:
		jv_cond += " AND je.company = %s"
		jv_params.append(company)
	if cost_center:
		jv_cond += " AND jea.cost_center = %s"
		jv_params.append(cost_center)

	jvs = frappe.db.sql(f"""
		SELECT je.company, je.name AS ref, je.posting_date AS date,
		       jea.account AS party, je.remark AS details,
		       jea.debit, jea.credit
		FROM `tabJournal Entry Account` jea
		INNER JOIN `tabJournal Entry` je ON je.name = jea.parent
		WHERE je.docstatus = 1 {jv_cond}
		ORDER BY je.posting_date
	""", tuple(jv_params), as_dict=True)

	jv_debits = [{**r, "amount": flt(r.debit)} for r in jvs if flt(r.debit) > 0]
	jv_credits = [{**r, "amount": flt(r.credit)} for r in jvs if flt(r.credit) > 0]

	total_sales = sum(flt(r.amount) for r in sales)
	total_purchase = sum(flt(r.amount) for r in purchases)
	total_jv_debit = sum(r["amount"] for r in jv_debits)
	total_jv_credit = sum(r["amount"] for r in jv_credits)

	return {
		"vehicle": vehicle,
		"sales": sales,
		"purchases": purchases,
		"jv_debits": jv_debits,
		"jv_credits": jv_credits,
		"total_sales": total_sales,
		"total_purchase": total_purchase,
		"total_jv_debit": total_jv_debit,
		"total_jv_credit": total_jv_credit,
		# same formula as the report: Sales - Purchase - JV Debits + JV Credits
		"gross_profit": total_sales - total_purchase - total_jv_debit + total_jv_credit,
	}


# ==================================================================
# Excel export of the popup (Vehicle Wise Consolidated Profit Report)
# ==================================================================

@frappe.whitelist()
def export_vehicle_statement(vehicle, from_date, to_date, company=None, cost_center=None):
	"""Download an Excel file with everything shown in the popup.
	All companies are included unless a company is passed."""
	import re
	from io import BytesIO

	from openpyxl import Workbook
	from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

	from frappe.utils import getdate

	if not frappe.get_doc("Report", "Vehicle-wise Gross Profit Report").is_permitted():
		frappe.throw(frappe._("You are not permitted to export this report."), frappe.PermissionError)

	d = get_vehicle_statement(vehicle, from_date, to_date, company, cost_center)

	wb = Workbook()
	ws = wb.active
	ws.title = "Statement"

	bold = Font(bold=True)
	title_font = Font(bold=True, size=14)
	head_fill = PatternFill("solid", fgColor="D9D9D9")
	sec_fill = PatternFill("solid", fgColor="F3F3F3")
	gp_fill = PatternFill("solid", fgColor="E8F5E9")
	money = "#,##0.00"
	date_fmt = "DD-MM-YYYY"
	thin = Side(style="thin", color="BFBFBF")
	border = Border(left=thin, right=thin, top=thin, bottom=thin)
	right = Alignment(horizontal="right")

	def put(sheet, row, col, value, number_format=None, font=None, fill=None, align=None, box=False):
		c = sheet.cell(row=row, column=col, value=value)
		if c.data_type == "f":  # text typed in ERPNext must never become a formula
			c.data_type = "s"
		if number_format:
			c.number_format = number_format
		if font:
			c.font = font
		if fill:
			c.fill = fill
		if align:
			c.alignment = align
		if box:
			c.border = border
		return c

	r = 1
	put(ws, r, 1, "Vehicle Wise Consolidated Profit Report", font=title_font)
	r += 2
	for label, value in (
		("Vehicle No", vehicle),
		("Company", company or "All companies"),
		("Cost Center", cost_center or "All"),
		("From Date", getdate(from_date)),
		("To Date", getdate(to_date)),
	):
		put(ws, r, 1, label, font=bold)
		put(ws, r, 2, value, number_format=date_fmt if label.endswith("Date") else None,
			align=Alignment(horizontal="left"))
		r += 1
	r += 1

	for col, head in enumerate(["Company", "Reference", "Date", "Details", "Amount"], 1):
		put(ws, r, col, head, font=bold, fill=head_fill, box=True,
			align=right if col == 5 else None)
	r += 1

	def section(title, rows, total_label, total):
		nonlocal r
		for col in range(1, 6):
			put(ws, r, col, title if col == 1 else None, font=bold, fill=sec_fill, box=True)
		r += 1
		for x in rows:
			details = (x.get("party") or "") + (" - " + x["details"] if x.get("details") else "")
			details = " ".join(details.split())  # remarks can contain line breaks
			put(ws, r, 1, x.get("company"), box=True)
			put(ws, r, 2, x.get("ref"), box=True)
			put(ws, r, 3, x.get("date"), number_format=date_fmt, box=True,
				align=Alignment(horizontal="left"))
			put(ws, r, 4, details, box=True)
			put(ws, r, 5, flt(x.get("amount")), number_format=money, box=True)
			r += 1
		put(ws, r, 4, total_label, font=bold, align=right)
		put(ws, r, 5, flt(total), number_format=money, font=bold)
		r += 2

	section("Sales", d["sales"], "Total Sales", d["total_sales"])
	section("Purchase", d["purchases"], "Total Purchase", d["total_purchase"])
	section("JV Debits", d["jv_debits"], "Total JV Debits", d["total_jv_debit"])
	section("JV Credits", d["jv_credits"], "Total JV Credits", d["total_jv_credit"])

	for col in range(1, 6):
		put(ws, r, col, None, fill=gp_fill)
	put(ws, r, 4, "Gross Profit", font=bold, fill=gp_fill, align=right)
	put(ws, r, 5, flt(d["gross_profit"]), number_format=money, font=bold, fill=gp_fill)

	for col, width in zip("ABCDE", (46, 24, 14, 70, 18)):
		ws.column_dimensions[col].width = width

	# ---- second sheet: totals per company ----
	by = {}
	for key, rows in (
		("sales", d["sales"]), ("purchase", d["purchases"]),
		("jv_debit", d["jv_debits"]), ("jv_credit", d["jv_credits"]),
	):
		for x in rows:
			t = by.setdefault(x.get("company") or "", dict(sales=0, purchase=0, jv_debit=0, jv_credit=0))
			t[key] += flt(x.get("amount"))

	ws2 = wb.create_sheet("Company Summary")
	heads = ["Company", "Sales", "Purchase", "JV Debit", "JV Credit", "Gross Profit"]
	for col, head in enumerate(heads, 1):
		put(ws2, 1, col, head, font=bold, fill=head_fill, box=True, align=right if col > 1 else None)

	row = 2
	tot = dict(sales=0, purchase=0, jv_debit=0, jv_credit=0, gp=0)
	for c in sorted(by):
		t = by[c]
		gp = t["sales"] - t["purchase"] - t["jv_debit"] + t["jv_credit"]
		vals = [c, t["sales"], t["purchase"], t["jv_debit"], t["jv_credit"], gp]
		for col, val in enumerate(vals, 1):
			put(ws2, row, col, val, number_format=money if col > 1 else None, box=True)
		for k, val in zip(("sales", "purchase", "jv_debit", "jv_credit", "gp"), vals[1:]):
			tot[k] += val
		row += 1
	if by:
		vals = ["Total", tot["sales"], tot["purchase"], tot["jv_debit"], tot["jv_credit"], tot["gp"]]
		for col, val in enumerate(vals, 1):
			put(ws2, row, col, val, number_format=money if col > 1 else None, font=bold, fill=gp_fill, box=True)
	for col, width in zip("ABCDEF", (46, 16, 16, 16, 16, 16)):
		ws2.column_dimensions[col].width = width

	out = BytesIO()
	wb.save(out)
	safe = re.sub(r"[^A-Za-z0-9_-]+", "_", str(vehicle)) or "vehicle"
	frappe.response["filename"] = f"Vehicle_{safe}_Consolidated_Profit.xlsx"
	frappe.response["filecontent"] = out.getvalue()
	frappe.response["type"] = "binary"