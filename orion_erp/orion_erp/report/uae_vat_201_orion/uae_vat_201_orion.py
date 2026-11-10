# # # Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# # # For license information, please see license.txt


# # import re

# # import frappe
# # from frappe import _
# # from frappe.utils import flt


# # def execute(filters=None):
# # 	filters = filters or {}
# # 	if filters.get("drilldown_key"):
# # 		return get_drilldown(filters)
# # 	columns = get_columns()
# # 	data, emirates, amounts_by_emirate = get_data(filters)
# # 	return columns, data


# # # ------------------------------------------------------------------
# # # Summary columns
# # # ------------------------------------------------------------------


# # def get_columns():
# # 	return [
# # 		{"fieldname": "no", "label": _("No"), "fieldtype": "Data", "width": 50},
# # 		{"fieldname": "legend", "label": _("Legend"), "fieldtype": "Data", "width": 300},
# # 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 125},
# # 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# # 	]


# # # ------------------------------------------------------------------
# # # Summary data
# # # ------------------------------------------------------------------


# # def get_data(filters=None):
# # 	data = []
# # 	emirates, amounts_by_emirate = append_vat_on_sales(data, filters)
# # 	append_vat_on_expenses(data, filters)
# # 	return data, emirates, amounts_by_emirate


# # def append_vat_on_sales(data, filters):
# # 	append_data(data, "", _("VAT on Sales and All Other Outputs"), "", "")

# # 	emirates, amounts_by_emirate = standard_rated_expenses_emiratewise(data, filters)

# # 	total_amounts = [amounts_by_emirate.get(e, {}).get("raw_amount", 0) for e in emirates]
# # 	total_vat_amounts = [amounts_by_emirate.get(e, {}).get("raw_vat_amount", 0) for e in emirates]

# # 	tourist_total = get_tourist_tax_return_total(filters)
# # 	tourist_tax = get_tourist_tax_return_tax(filters)
# # 	append_data(
# # 		data,
# # 		"2",
# # 		_("Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme"),
# # 		frappe.format((-1) * tourist_total, "Currency"),
# # 		frappe.format((-1) * tourist_tax, "Currency"),
# # 		drilldown_key="tourist_refund",
# # 		raw_amount=(-1) * tourist_total,
# # 		raw_vat_amount=(-1) * tourist_tax,
# # 	)
# # 	total_amounts.append((-1) * tourist_total)
# # 	total_vat_amounts.append((-1) * tourist_tax)

# # 	rc_total = get_reverse_charge_total(filters)
# # 	rc_tax = get_reverse_charge_tax(filters)
# # 	append_data(
# # 		data,
# # 		"3",
# # 		_("Supplies subject to the reverse charge provision"),
# # 		frappe.format(rc_total, "Currency"),
# # 		frappe.format(rc_tax, "Currency"),
# # 		drilldown_key="reverse_charge_sales",
# # 		raw_amount=rc_total,
# # 		raw_vat_amount=rc_tax,
# # 	)
# # 	total_amounts.append(rc_total)
# # 	total_vat_amounts.append(rc_tax)

# # 	zero_total = get_zero_rated_total(filters)
# # 	append_data(
# # 		data,
# # 		"4",
# # 		_("Zero Rated"),
# # 		frappe.format(zero_total, "Currency"),
# # 		"-",
# # 		drilldown_key="zero_rated",
# # 		raw_amount=zero_total,
# # 		raw_vat_amount=0,
# # 	)
# # 	total_amounts.append(zero_total)

# # 	exempt_total = get_exempt_total(filters)
# # 	append_data(
# # 		data,
# # 		"5",
# # 		_("Exempt Supplies"),
# # 		frappe.format(exempt_total, "Currency"),
# # 		"-",
# # 		drilldown_key="exempt",
# # 		raw_amount=exempt_total,
# # 		raw_vat_amount=0,
# # 	)
# # 	total_amounts.append(exempt_total)

# # 	append_data(
# # 		data,
# # 		"",
# # 		_("Total VAT on Sales and All Other Outputs"),
# # 		frappe.format(sum(total_amounts), "Currency"),
# # 		frappe.format(sum(total_vat_amounts), "Currency"),
# # 	)

# # 	append_data(data, "", "", "", "")

# # 	return emirates, amounts_by_emirate


# # def standard_rated_expenses_emiratewise(data, filters):
# # 	total_emiratewise = get_total_emiratewise(filters)
# # 	emirates = get_emirates()
# # 	amounts_by_emirate = {}
# # 	for emirate, amount, vat in total_emiratewise:
# # 		amounts_by_emirate[emirate] = {
# # 			"legend": emirate,
# # 			"raw_amount": flt(amount),
# # 			"raw_vat_amount": flt(vat),
# # 			"amount": frappe.format(amount, "Currency"),
# # 			"vat_amount": frappe.format(vat, "Currency"),
# # 		}
# # 	amounts_by_emirate = append_emiratewise_expenses(data, emirates, amounts_by_emirate)
# # 	return emirates, amounts_by_emirate


# # def append_emiratewise_expenses(data, emirates, amounts_by_emirate):
# # 	for no, emirate in enumerate(emirates, 97):
# # 		key = "standard_rated_{0}".format(emirate)
# # 		if emirate in amounts_by_emirate:
# # 			amounts_by_emirate[emirate]["no"] = _("1{0}").format(chr(no))
# # 			amounts_by_emirate[emirate]["legend"] = _("Standard rated supplies in {0}").format(emirate)
# # 			amounts_by_emirate[emirate]["drilldown_key"] = key
# # 			data.append(amounts_by_emirate[emirate])
# # 		else:
# # 			append_data(
# # 				data,
# # 				_("1{0}").format(chr(no)),
# # 				_("Standard rated supplies in {0}").format(emirate),
# # 				frappe.format(0, "Currency"),
# # 				frappe.format(0, "Currency"),
# # 				drilldown_key=key,
# # 				raw_amount=0,
# # 				raw_vat_amount=0,
# # 			)
# # 	return amounts_by_emirate


# # def append_vat_on_expenses(data, filters):
# # 	append_data(data, "", _("VAT on Expenses and All Other Inputs"), "", "")

# # 	std_exp_total = get_standard_rated_expenses_total(filters)
# # 	std_exp_tax = get_standard_rated_expenses_tax(filters)
# # 	append_data(
# # 		data,
# # 		"9",
# # 		_("Standard Rated Expenses"),
# # 		frappe.format(std_exp_total, "Currency"),
# # 		frappe.format(std_exp_tax, "Currency"),
# # 		drilldown_key="standard_rated_expenses",
# # 		raw_amount=std_exp_total,
# # 		raw_vat_amount=std_exp_tax,
# # 	)

# # 	rc_rec_total = get_reverse_charge_recoverable_total(filters)
# # 	rc_rec_tax = get_reverse_charge_recoverable_tax(filters)
# # 	append_data(
# # 		data,
# # 		"10",
# # 		_("Supplies subject to the reverse charge provision"),
# # 		frappe.format(rc_rec_total, "Currency"),
# # 		frappe.format(rc_rec_tax, "Currency"),
# # 		drilldown_key="reverse_charge_expenses",
# # 		raw_amount=rc_rec_total,
# # 		raw_vat_amount=rc_rec_tax,
# # 	)

# # 	append_data(
# # 		data,
# # 		"",
# # 		_("Total VAT on Expenses and All Other Inputs"),
# # 		frappe.format(std_exp_total + rc_rec_total, "Currency"),
# # 		frappe.format(std_exp_tax + rc_rec_tax, "Currency"),
# # 	)


# # def append_data(data, no, legend, amount, vat_amount, drilldown_key=None, raw_amount=0, raw_vat_amount=0):
# # 	row = {"no": no, "legend": legend, "amount": amount, "vat_amount": vat_amount}
# # 	if drilldown_key:
# # 		row["drilldown_key"] = drilldown_key
# # 		row["raw_amount"] = raw_amount
# # 		row["raw_vat_amount"] = raw_vat_amount
# # 	data.append(row)


# # # ==================================================================
# # # Drill-down
# # # ==================================================================


# # def get_drilldown(filters):
# # 	key = filters.get("drilldown_key")
# # 	company = filters.get("company")
# # 	from_date = filters.get("from_date")
# # 	to_date = filters.get("to_date")

# # 	purchase_keys = ("standard_rated_expenses", "reverse_charge_expenses", "expenses_total")
# # 	if key in purchase_keys:
# # 		columns, data = _get_purchase_detail(key, company, from_date, to_date)
# # 	elif key == "reverse_charge_sales":
# # 		columns = _purchase_detail_columns()
# # 		data = _rc_sales_detail(company, from_date, to_date)
# # 	else:
# # 		columns, data = _get_sales_detail(key, company, from_date, to_date)

# # 	return columns, data, None, None, None, True


# # def _get_sales_detail(key, company, from_date, to_date):
# # 	if key.startswith("standard_rated_"):
# # 		emirate = key[len("standard_rated_") :]
# # 		return _sales_invoice_breakdown(company, from_date, to_date, emirate=emirate)
# # 	elif key == "tourist_refund":
# # 		return _sales_invoice_breakdown(company, from_date, to_date, tourist_only=True)
# # 	elif key == "zero_rated":
# # 		return _sales_invoice_breakdown(company, from_date, to_date, is_zero_rated=True)
# # 	elif key == "exempt":
# # 		return _sales_invoice_breakdown(company, from_date, to_date, is_exempt=True)
# # 	elif key == "sales_total":
# # 		return _sales_invoice_breakdown(company, from_date, to_date)
# # 	return [], []


# # def _get_purchase_detail(key, company, from_date, to_date):
# # 	columns = _purchase_detail_columns()
# # 	if key == "standard_rated_expenses":
# # 		data = _std_expenses_detail(company, from_date, to_date)
# # 	elif key == "reverse_charge_expenses":
# # 		data = _rc_expenses_detail(company, from_date, to_date)
# # 	elif key == "expenses_total":
# # 		data = _all_expenses_detail(company, from_date, to_date)
# # 	else:
# # 		data = []
# # 	return columns, data


# # def _purchase_detail_columns():
# # 	return [
# # 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# # 		{
# # 			"fieldname": "doc_name",
# # 			"label": _("Document No"),
# # 			"fieldtype": "Dynamic Link",
# # 			"options": "doc_type",
# # 			"width": 180,
# # 		},
# # 		{"fieldname": "party", "label": _("Party"), "fieldtype": "Data", "width": 200},
# # 		{"fieldname": "item", "label": _("Item"), "fieldtype": "Data", "width": 200},
# # 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 130},
# # 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# # 	]


# # def _account_fieldname(account):
# # 	"""Sanitize an account name for use as a column fieldname."""
# # 	return "acc_" + re.sub(r"[^a-zA-Z0-9_]", "_", account)


# # def _sales_invoice_breakdown(
# # 	company, from_date, to_date, emirate=None, is_zero_rated=False, is_exempt=False, tourist_only=False
# # ):
# # 	"""Account-wise breakdown of qualifying Sales Invoices."""
# # 	si_cond, si_params = _si_conditions(company, from_date, to_date)

# # 	if tourist_only:
# # 		invoices = frappe.db.sql_list(
# # 			"SELECT si.name FROM `tabSales Invoice` si WHERE 1=1 "
# # 			+ si_cond + " AND si.tourist_tax_return > 0",
# # 			tuple(si_params),
# # 		)
# # 	else:
# # 		item_cond = ""
# # 		item_params = []
# # 		if emirate:
# # 			item_cond += " AND si.vat_emirate = %s"
# # 			item_params.append(emirate)
# # 		if is_zero_rated:
# # 			item_cond += " AND sii.is_zero_rated = 1"
# # 		elif is_exempt:
# # 			item_cond += " AND sii.is_exempt = 1"
# # 		else:
# # 			item_cond += " AND sii.is_exempt != 1 AND sii.is_zero_rated != 1"

# # 		invoices = frappe.db.sql_list(
# # 			"SELECT DISTINCT si.name FROM `tabSales Invoice Item` sii "
# # 			"INNER JOIN `tabSales Invoice` si ON si.name = sii.parent "
# # 			"WHERE 1=1 " + si_cond + item_cond,
# # 			tuple(si_params + item_params),
# # 		)

# # 	if not invoices:
# # 		return _sales_breakdown_columns([], []), []

# # 	invoices_tuple = tuple(invoices)

# # 	headers = frappe.db.sql(
# # 		"""
# # 		SELECT si.name AS sales_invoice, si.posting_date, si.customer_name AS customer,
# # 		       si.debit_to AS receivable_account, si.vat_emirate
# # 		FROM `tabSales Invoice` si
# # 		WHERE si.docstatus = 1 AND si.name IN %s
# # 		ORDER BY si.posting_date
# # 		""",
# # 		(invoices_tuple,),
# # 		as_dict=True,
# # 	)

# # 	items = frappe.db.sql(
# # 		"""
# # 		SELECT sii.parent AS sales_invoice, sii.income_account, sii.base_net_amount
# # 		FROM `tabSales Invoice Item` sii
# # 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# # 		WHERE si.docstatus = 1 AND sii.parent IN %s
# # 		""",
# # 		(invoices_tuple,),
# # 		as_dict=True,
# # 	)

# # 	taxes = frappe.db.sql(
# # 		"""
# # 		SELECT stc.parent AS sales_invoice, stc.account_head, stc.base_tax_amount
# # 		FROM `tabSales Taxes and Charges` stc
# # 		INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
# # 		WHERE si.docstatus = 1 AND stc.parent IN %s
# # 		""",
# # 		(invoices_tuple,),
# # 		as_dict=True,
# # 	)

# # 	income_accounts = sorted({r.income_account for r in items if r.income_account})
# # 	tax_accounts = sorted({r.account_head for r in taxes if r.account_head})

# # 	item_map = {}
# # 	for r in items:
# # 		item_map.setdefault(r.sales_invoice, []).append(r)

# # 	tax_map = {}
# # 	for r in taxes:
# # 		tax_map.setdefault(r.sales_invoice, []).append(r)

# # 	data = []
# # 	for h in headers:
# # 		row = {
# # 			"voucher_type": "Sales Invoice",
# # 			"sales_invoice": h.sales_invoice,
# # 			"posting_date": h.posting_date,
# # 			"customer": h.customer,
# # 			"receivable_account": h.receivable_account,
# # 			"vat_emirate": h.vat_emirate,
# # 		}
# # 		for acc in income_accounts:
# # 			row[_account_fieldname(acc)] = 0
# # 		for acc in tax_accounts:
# # 			row[_account_fieldname(acc)] = 0

# # 		net_total = 0
# # 		for it in item_map.get(h.sales_invoice, []):
# # 			net_total += flt(it.base_net_amount)
# # 			if it.income_account:
# # 				row[_account_fieldname(it.income_account)] = flt(row[_account_fieldname(it.income_account)]) + flt(
# # 					it.base_net_amount
# # 				)

# # 		tax_total = 0
# # 		for t in tax_map.get(h.sales_invoice, []):
# # 			tax_total += flt(t.base_tax_amount)
# # 			if t.account_head:
# # 				row[_account_fieldname(t.account_head)] = flt(row[_account_fieldname(t.account_head)]) + flt(
# # 					t.base_tax_amount
# # 				)

# # 		row["net_total"] = flt(net_total)
# # 		row["tax_total"] = flt(tax_total)
# # 		row["grand_total"] = flt(net_total + tax_total)
# # 		data.append(row)

# # 	columns = _sales_breakdown_columns(income_accounts, tax_accounts)
# # 	return columns, data


# # def _sales_breakdown_columns(income_accounts, tax_accounts):
# # 	columns = [
# # 		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 110},
# # 		{
# # 			"fieldname": "sales_invoice",
# # 			"label": _("Sales Invoice No"),
# # 			"fieldtype": "Link",
# # 			"options": "Sales Invoice",
# # 			"width": 150,
# # 		},
# # 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# # 		{"fieldname": "vat_emirate", "label": _("VAT Emirates"), "fieldtype": "Data", "width": 140},
# # 		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 220},
# # 		{"fieldname": "receivable_account", "label": _("Receivable Account"), "fieldtype": "Data", "width": 220},
# # 	]
# # 	for acc in income_accounts:
# # 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# # 	for acc in tax_accounts:
# # 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# # 	columns.extend(
# # 		[
# # 			{"fieldname": "net_total", "label": _("Net Total"), "fieldtype": "Currency", "width": 140},
# # 			{"fieldname": "tax_total", "label": _("Tax Total"), "fieldtype": "Currency", "width": 140},
# # 			{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 150},
# # 		]
# # 	)
# # 	return columns


# # # ------------------------------------------------------------------
# # # Condition builders
# # # ------------------------------------------------------------------


# # def _si_conditions(company, from_date, to_date):
# # 	cond = "AND si.docstatus = 1"
# # 	params = []
# # 	if company:
# # 		cond += " AND si.company = %s"
# # 		params.append(company)
# # 	if from_date:
# # 		cond += " AND si.posting_date >= %s"
# # 		params.append(from_date)
# # 	if to_date:
# # 		cond += " AND si.posting_date <= %s"
# # 		params.append(to_date)
# # 	return cond, params


# # def _pi_conditions(company, from_date, to_date):
# # 	cond = "AND pi.docstatus = 1"
# # 	params = []
# # 	if company:
# # 		cond += " AND pi.company = %s"
# # 		params.append(company)
# # 	if from_date:
# # 		cond += " AND pi.posting_date >= %s"
# # 		params.append(from_date)
# # 	if to_date:
# # 		cond += " AND pi.posting_date <= %s"
# # 		params.append(to_date)
# # 	return cond, params


# # def _gl_conditions(company):
# # 	cond = "AND gl.docstatus = 1"
# # 	params = []
# # 	if company:
# # 		cond += " AND gl.account IN (SELECT account FROM `tabUAE VAT Account` WHERE parent = %s)"
# # 		params.append(company)
# # 	return cond, params


# # # ------------------------------------------------------------------
# # # Sales-side detail queries
# # # ------------------------------------------------------------------


# # def _rc_sales_detail(company, from_date, to_date):
# # 	cond, params = _pi_conditions(company, from_date, to_date)
# # 	gl_cond, gl_params = _gl_conditions(company)
# # 	cond += " AND pi.reverse_charge = 'Y' " + gl_cond
# # 	params.extend(gl_params)

# # 	return frappe.db.sql(
# # 		f"""
# # 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# # 		       pi.supplier_name AS party, '' AS item,
# # 		       pi.base_total AS amount, SUM(gl.debit) AS vat_amount
# # 		FROM `tabPurchase Invoice` pi
# # 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# # 		WHERE 1=1 {cond}
# # 		GROUP BY pi.name
# # 		ORDER BY pi.posting_date
# # 	""",
# # 		tuple(params),
# # 		as_dict=True,
# # 	)


# # # ------------------------------------------------------------------
# # # Purchase-side detail queries
# # # ------------------------------------------------------------------


# # def _std_expenses_detail(company, from_date, to_date):
# # 	cond, params = _pi_conditions(company, from_date, to_date)
# # 	cond += " AND pi.recoverable_standard_rated_expenses > 0"

# # 	return frappe.db.sql(
# # 		f"""
# # 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# # 		       pi.supplier_name AS party, '' AS item,
# # 		       pi.base_total AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
# # 		FROM `tabPurchase Invoice` pi
# # 		WHERE 1=1 {cond}
# # 		ORDER BY pi.posting_date
# # 	""",
# # 		tuple(params),
# # 		as_dict=True,
# # 	)


# # def _rc_expenses_detail(company, from_date, to_date):
# # 	cond, params = _pi_conditions(company, from_date, to_date)
# # 	gl_cond, gl_params = _gl_conditions(company)
# # 	cond += " AND pi.reverse_charge = 'Y' AND pi.recoverable_reverse_charge > 0 " + gl_cond
# # 	params.extend(gl_params)

# # 	return frappe.db.sql(
# # 		f"""
# # 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# # 		       pi.supplier_name AS party, '' AS item,
# # 		       pi.base_total AS amount,
# # 		       SUM(gl.debit * pi.recoverable_reverse_charge / 100) AS vat_amount
# # 		FROM `tabPurchase Invoice` pi
# # 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# # 		WHERE 1=1 {cond}
# # 		GROUP BY pi.name
# # 		ORDER BY pi.posting_date
# # 	""",
# # 		tuple(params),
# # 		as_dict=True,
# # 	)


# # # ------------------------------------------------------------------
# # # Combined detail queries
# # # ------------------------------------------------------------------


# # def _all_expenses_detail(company, from_date, to_date):
# # 	data = []
# # 	data.extend(_std_expenses_detail(company, from_date, to_date))
# # 	data.extend(_rc_expenses_detail(company, from_date, to_date))
# # 	return data


# # # ==================================================================
# # # Original helper functions
# # # ==================================================================


# # def get_total_emiratewise(filters):
# # 	conditions = get_conditions(filters)
# # 	try:
# # 		return frappe.db.sql(
# # 			f"""
# # 			select
# # 				s.vat_emirate as emirate, sum(i.base_net_amount) as total, sum(i.tax_amount)
# # 			from
# # 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# # 			on
# # 				i.parent = s.name
# # 			where
# # 				s.docstatus = 1 and i.is_exempt != 1 and i.is_zero_rated != 1
# # 				{conditions}
# # 			group by
# # 				s.vat_emirate;
# # 			""",
# # 			filters,
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_emirates():
# # 	return ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]


# # def get_filters(filters):
# # 	query_filters = []
# # 	if filters.get("company"):
# # 		query_filters.append(["company", "=", filters["company"]])
# # 	if filters.get("from_date"):
# # 		query_filters.append(["posting_date", ">=", filters["from_date"]])
# # 	if filters.get("from_date"):
# # 		query_filters.append(["posting_date", "<=", filters["to_date"]])
# # 	return query_filters


# # def get_reverse_charge_total(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["reverse_charge", "=", "Y"])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_reverse_charge_tax(filters):
# # 	conditions = get_conditions_join(filters)
# # 	return (
# # 		frappe.db.sql(
# # 			f"""
# # 		select sum(debit)  from
# # 			`tabPurchase Invoice` p inner join `tabGL Entry` gl
# # 		on
# # 			gl.voucher_no =  p.name
# # 		where
# # 			p.reverse_charge = "Y"
# # 			and p.docstatus = 1
# # 			and gl.docstatus = 1
# # 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# # 			{conditions} ;
# # 		""",
# # 			filters,
# # 		)[0][0]
# # 		or 0
# # 	)


# # def get_reverse_charge_recoverable_total(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["reverse_charge", "=", "Y"])
# # 	query_filters.append(["recoverable_reverse_charge", ">", "0"])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_reverse_charge_recoverable_tax(filters):
# # 	conditions = get_conditions_join(filters)
# # 	return (
# # 		frappe.db.sql(
# # 			f"""
# # 		select
# # 			sum(debit * p.recoverable_reverse_charge / 100)
# # 		from
# # 			`tabPurchase Invoice` p  inner join `tabGL Entry` gl
# # 		on
# # 			gl.voucher_no = p.name
# # 		where
# # 			p.reverse_charge = "Y"
# # 			and p.docstatus = 1
# # 			and p.recoverable_reverse_charge > 0
# # 			and gl.docstatus = 1
# # 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# # 			{conditions} ;
# # 		""",
# # 			filters,
# # 		)[0][0]
# # 		or 0
# # 	)


# # def get_conditions_join(filters):
# # 	conditions = ""
# # 	for opts in (
# # 		("company", " and p.company=%(company)s"),
# # 		("from_date", " and p.posting_date>=%(from_date)s"),
# # 		("to_date", " and p.posting_date<=%(to_date)s"),
# # 	):
# # 		if filters.get(opts[0]):
# # 			conditions += opts[1]
# # 	return conditions


# # def get_standard_rated_expenses_total(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_standard_rated_expenses_tax(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Purchase Invoice",
# # 				filters=query_filters,
# # 				fields=["sum(recoverable_standard_rated_expenses)"],
# # 				as_list=True,
# # 				limit=1,
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_tourist_tax_return_total(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["tourist_tax_return", ">", 0])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Sales Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_tourist_tax_return_tax(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["tourist_tax_return", ">", 0])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Sales Invoice",
# # 				filters=query_filters,
# # 				fields=["sum(tourist_tax_return)"],
# # 				as_list=True,
# # 				limit=1,
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_zero_rated_total(filters):
# # 	conditions = get_conditions(filters)
# # 	try:
# # 		return (
# # 			frappe.db.sql(
# # 				f"""
# # 			select
# # 				sum(i.base_net_amount) as total
# # 			from
# # 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# # 			on
# # 				i.parent = s.name
# # 			where
# # 				s.docstatus = 1 and  i.is_zero_rated = 1
# # 				{conditions} ;
# # 			""",
# # 				filters,
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_exempt_total(filters):
# # 	conditions = get_conditions(filters)
# # 	try:
# # 		return (
# # 			frappe.db.sql(
# # 				f"""
# # 			select
# # 				sum(i.base_net_amount) as total
# # 			from
# # 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# # 			on
# # 				i.parent = s.name
# # 			where
# # 				s.docstatus = 1 and  i.is_exempt = 1
# # 				{conditions} ;
# # 			""",
# # 				filters,
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_conditions(filters):
# # 	conditions = ""
# # 	for opts in (
# # 		("company", " and company=%(company)s"),
# # 		("from_date", " and posting_date>=%(from_date)s"),
# # 		("to_date", " and posting_date<=%(to_date)s"),
# # 	):
# # 		if filters.get(opts[0]):
# # 			conditions += opts[1]
# # 	return conditions


# # Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# # For license information, please see license.txt


# # import json
# # import re

# # import frappe
# # from frappe import _
# # from frappe.utils import add_days, add_months, flt, getdate


# # def execute(filters=None):
# # 	filters = filters or {}
# # 	if filters.get("drilldown_key") == "vat_transactions":
# # 		return get_vat_transactions(filters)
# # 	if filters.get("drilldown_key"):
# # 		return get_drilldown(filters)
# # 	columns = get_columns()
# # 	data, emirates, amounts_by_emirate = get_data(filters)
# # 	return columns, data


# # # ------------------------------------------------------------------
# # # Summary columns
# # # ------------------------------------------------------------------


# # def get_columns():
# # 	return [
# # 		{"fieldname": "no", "label": _("No"), "fieldtype": "Data", "width": 50},
# # 		{"fieldname": "legend", "label": _("Legend"), "fieldtype": "Data", "width": 300},
# # 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 125},
# # 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# # 	]


# # # ------------------------------------------------------------------
# # # Summary data
# # # ------------------------------------------------------------------


# # def get_data(filters=None):
# # 	data = []
# # 	emirates, amounts_by_emirate = append_vat_on_sales(data, filters)
# # 	append_vat_on_expenses(data, filters)
# # 	return data, emirates, amounts_by_emirate


# # def append_vat_on_sales(data, filters):
# # 	append_data(data, "", _("VAT on Sales and All Other Outputs"), "", "")

# # 	emirates, amounts_by_emirate = standard_rated_expenses_emiratewise(data, filters)

# # 	total_amounts = [amounts_by_emirate.get(e, {}).get("raw_amount", 0) for e in emirates]
# # 	total_vat_amounts = [amounts_by_emirate.get(e, {}).get("raw_vat_amount", 0) for e in emirates]

# # 	tourist_total = get_tourist_tax_return_total(filters)
# # 	tourist_tax = get_tourist_tax_return_tax(filters)
# # 	append_data(
# # 		data,
# # 		"2",
# # 		_("Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme"),
# # 		frappe.format((-1) * tourist_total, "Currency"),
# # 		frappe.format((-1) * tourist_tax, "Currency"),
# # 		drilldown_key="tourist_refund",
# # 		raw_amount=(-1) * tourist_total,
# # 		raw_vat_amount=(-1) * tourist_tax,
# # 	)
# # 	total_amounts.append((-1) * tourist_total)
# # 	total_vat_amounts.append((-1) * tourist_tax)

# # 	rc_total = get_reverse_charge_total(filters)
# # 	rc_tax = get_reverse_charge_tax(filters)
# # 	append_data(
# # 		data,
# # 		"3",
# # 		_("Supplies subject to the reverse charge provision"),
# # 		frappe.format(rc_total, "Currency"),
# # 		frappe.format(rc_tax, "Currency"),
# # 		drilldown_key="reverse_charge_sales",
# # 		raw_amount=rc_total,
# # 		raw_vat_amount=rc_tax,
# # 	)
# # 	total_amounts.append(rc_total)
# # 	total_vat_amounts.append(rc_tax)

# # 	zero_total = get_zero_rated_total(filters)
# # 	append_data(
# # 		data,
# # 		"4",
# # 		_("Zero Rated"),
# # 		frappe.format(zero_total, "Currency"),
# # 		"-",
# # 		drilldown_key="zero_rated",
# # 		raw_amount=zero_total,
# # 		raw_vat_amount=0,
# # 	)
# # 	total_amounts.append(zero_total)

# # 	exempt_total = get_exempt_total(filters)
# # 	append_data(
# # 		data,
# # 		"5",
# # 		_("Exempt Supplies"),
# # 		frappe.format(exempt_total, "Currency"),
# # 		"-",
# # 		drilldown_key="exempt",
# # 		raw_amount=exempt_total,
# # 		raw_vat_amount=0,
# # 	)
# # 	total_amounts.append(exempt_total)

# # 	append_data(
# # 		data,
# # 		"",
# # 		_("Total VAT on Sales and All Other Outputs"),
# # 		frappe.format(sum(total_amounts), "Currency"),
# # 		frappe.format(sum(total_vat_amounts), "Currency"),
# # 	)

# # 	append_data(data, "", "", "", "")

# # 	return emirates, amounts_by_emirate


# # def standard_rated_expenses_emiratewise(data, filters):
# # 	total_emiratewise = get_total_emiratewise(filters)
# # 	emirates = get_emirates()
# # 	amounts_by_emirate = {}
# # 	for emirate, amount, vat in total_emiratewise:
# # 		amounts_by_emirate[emirate] = {
# # 			"legend": emirate,
# # 			"raw_amount": flt(amount),
# # 			"raw_vat_amount": flt(vat),
# # 			"amount": frappe.format(amount, "Currency"),
# # 			"vat_amount": frappe.format(vat, "Currency"),
# # 		}
# # 	amounts_by_emirate = append_emiratewise_expenses(data, emirates, amounts_by_emirate)
# # 	return emirates, amounts_by_emirate


# # def append_emiratewise_expenses(data, emirates, amounts_by_emirate):
# # 	for no, emirate in enumerate(emirates, 97):
# # 		key = "standard_rated_{0}".format(emirate)
# # 		if emirate in amounts_by_emirate:
# # 			amounts_by_emirate[emirate]["no"] = _("1{0}").format(chr(no))
# # 			amounts_by_emirate[emirate]["legend"] = _("Standard rated supplies in {0}").format(emirate)
# # 			amounts_by_emirate[emirate]["drilldown_key"] = key
# # 			data.append(amounts_by_emirate[emirate])
# # 		else:
# # 			append_data(
# # 				data,
# # 				_("1{0}").format(chr(no)),
# # 				_("Standard rated supplies in {0}").format(emirate),
# # 				frappe.format(0, "Currency"),
# # 				frappe.format(0, "Currency"),
# # 				drilldown_key=key,
# # 				raw_amount=0,
# # 				raw_vat_amount=0,
# # 			)
# # 	return amounts_by_emirate


# # def append_vat_on_expenses(data, filters):
# # 	append_data(data, "", _("VAT on Expenses and All Other Inputs"), "", "")

# # 	std_exp_total = get_standard_rated_expenses_total(filters)
# # 	std_exp_tax = get_standard_rated_expenses_tax(filters)
# # 	append_data(
# # 		data,
# # 		"9",
# # 		_("Standard Rated Expenses"),
# # 		frappe.format(std_exp_total, "Currency"),
# # 		frappe.format(std_exp_tax, "Currency"),
# # 		drilldown_key="standard_rated_expenses",
# # 		raw_amount=std_exp_total,
# # 		raw_vat_amount=std_exp_tax,
# # 	)

# # 	rc_rec_total = get_reverse_charge_recoverable_total(filters)
# # 	rc_rec_tax = get_reverse_charge_recoverable_tax(filters)
# # 	append_data(
# # 		data,
# # 		"10",
# # 		_("Supplies subject to the reverse charge provision"),
# # 		frappe.format(rc_rec_total, "Currency"),
# # 		frappe.format(rc_rec_tax, "Currency"),
# # 		drilldown_key="reverse_charge_expenses",
# # 		raw_amount=rc_rec_total,
# # 		raw_vat_amount=rc_rec_tax,
# # 	)

# # 	append_data(
# # 		data,
# # 		"",
# # 		_("Total VAT on Expenses and All Other Inputs"),
# # 		frappe.format(std_exp_total + rc_rec_total, "Currency"),
# # 		frappe.format(std_exp_tax + rc_rec_tax, "Currency"),
# # 	)


# # def append_data(data, no, legend, amount, vat_amount, drilldown_key=None, raw_amount=0, raw_vat_amount=0):
# # 	row = {"no": no, "legend": legend, "amount": amount, "vat_amount": vat_amount}
# # 	if drilldown_key:
# # 		row["drilldown_key"] = drilldown_key
# # 		row["raw_amount"] = raw_amount
# # 		row["raw_vat_amount"] = raw_vat_amount
# # 	data.append(row)


# # # ==================================================================
# # # Drill-down
# # # ==================================================================


# # def get_drilldown(filters):
# # 	key = filters.get("drilldown_key")
# # 	company = filters.get("company")
# # 	from_date = filters.get("from_date")
# # 	to_date = filters.get("to_date")

# # 	purchase_keys = ("standard_rated_expenses", "reverse_charge_expenses", "expenses_total")
# # 	if key in purchase_keys:
# # 		columns, data = _get_purchase_detail(key, company, from_date, to_date)
# # 	elif key == "reverse_charge_sales":
# # 		columns = _purchase_detail_columns()
# # 		data = _rc_sales_detail(company, from_date, to_date)
# # 	else:
# # 		columns, data = _get_sales_detail(key, company, from_date, to_date)

# # 	return columns, data, None, None, None, True


# # def _get_sales_detail(key, company, from_date, to_date):
# # 	if key.startswith("standard_rated_"):
# # 		emirate = key[len("standard_rated_") :]
# # 		return _sales_invoice_breakdown(company, from_date, to_date, emirate=emirate)
# # 	elif key == "tourist_refund":
# # 		return _sales_invoice_breakdown(company, from_date, to_date, tourist_only=True)
# # 	elif key == "zero_rated":
# # 		return _sales_invoice_breakdown(company, from_date, to_date, is_zero_rated=True)
# # 	elif key == "exempt":
# # 		return _sales_invoice_breakdown(company, from_date, to_date, is_exempt=True)
# # 	elif key == "sales_total":
# # 		return _sales_invoice_breakdown(company, from_date, to_date)
# # 	return [], []


# # def _get_purchase_detail(key, company, from_date, to_date):
# # 	columns = _purchase_detail_columns()
# # 	if key == "standard_rated_expenses":
# # 		data = _std_expenses_detail(company, from_date, to_date)
# # 	elif key == "reverse_charge_expenses":
# # 		data = _rc_expenses_detail(company, from_date, to_date)
# # 	elif key == "expenses_total":
# # 		data = _all_expenses_detail(company, from_date, to_date)
# # 	else:
# # 		data = []
# # 	return columns, data


# # def _purchase_detail_columns():
# # 	return [
# # 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# # 		{
# # 			"fieldname": "doc_name",
# # 			"label": _("Document No"),
# # 			"fieldtype": "Dynamic Link",
# # 			"options": "doc_type",
# # 			"width": 180,
# # 		},
# # 		{"fieldname": "party", "label": _("Party"), "fieldtype": "Data", "width": 200},
# # 		{"fieldname": "item", "label": _("Item"), "fieldtype": "Data", "width": 200},
# # 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 130},
# # 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# # 	]


# # def _account_fieldname(account):
# # 	"""Sanitize an account name for use as a column fieldname."""
# # 	return "acc_" + re.sub(r"[^a-zA-Z0-9_]", "_", account)


# # def _sales_invoice_breakdown(
# # 	company, from_date, to_date, emirate=None, is_zero_rated=False, is_exempt=False, tourist_only=False
# # ):
# # 	"""Account-wise breakdown of qualifying Sales Invoices."""
# # 	si_cond, si_params = _si_conditions(company, from_date, to_date)

# # 	if tourist_only:
# # 		invoices = frappe.db.sql_list(
# # 			"SELECT si.name FROM `tabSales Invoice` si WHERE 1=1 "
# # 			+ si_cond + " AND si.tourist_tax_return > 0",
# # 			tuple(si_params),
# # 		)
# # 	else:
# # 		item_cond = ""
# # 		item_params = []
# # 		if emirate:
# # 			item_cond += " AND si.vat_emirate = %s"
# # 			item_params.append(emirate)
# # 		if is_zero_rated:
# # 			item_cond += " AND sii.is_zero_rated = 1"
# # 		elif is_exempt:
# # 			item_cond += " AND sii.is_exempt = 1"
# # 		else:
# # 			item_cond += " AND sii.is_exempt != 1 AND sii.is_zero_rated != 1"

# # 		invoices = frappe.db.sql_list(
# # 			"SELECT DISTINCT si.name FROM `tabSales Invoice Item` sii "
# # 			"INNER JOIN `tabSales Invoice` si ON si.name = sii.parent "
# # 			"WHERE 1=1 " + si_cond + item_cond,
# # 			tuple(si_params + item_params),
# # 		)

# # 	if not invoices:
# # 		return _sales_breakdown_columns([], []), []

# # 	invoices_tuple = tuple(invoices)

# # 	headers = frappe.db.sql(
# # 		"""
# # 		SELECT si.name AS sales_invoice, si.posting_date, si.customer_name AS customer,
# # 		       si.debit_to AS receivable_account, si.vat_emirate
# # 		FROM `tabSales Invoice` si
# # 		WHERE si.docstatus = 1 AND si.name IN %s
# # 		ORDER BY si.posting_date
# # 		""",
# # 		(invoices_tuple,),
# # 		as_dict=True,
# # 	)

# # 	items = frappe.db.sql(
# # 		"""
# # 		SELECT sii.parent AS sales_invoice, sii.income_account, sii.base_net_amount
# # 		FROM `tabSales Invoice Item` sii
# # 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# # 		WHERE si.docstatus = 1 AND sii.parent IN %s
# # 		""",
# # 		(invoices_tuple,),
# # 		as_dict=True,
# # 	)

# # 	taxes = frappe.db.sql(
# # 		"""
# # 		SELECT stc.parent AS sales_invoice, stc.account_head, stc.base_tax_amount
# # 		FROM `tabSales Taxes and Charges` stc
# # 		INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
# # 		WHERE si.docstatus = 1 AND stc.parent IN %s
# # 		""",
# # 		(invoices_tuple,),
# # 		as_dict=True,
# # 	)

# # 	income_accounts = sorted({r.income_account for r in items if r.income_account})
# # 	tax_accounts = sorted({r.account_head for r in taxes if r.account_head})

# # 	item_map = {}
# # 	for r in items:
# # 		item_map.setdefault(r.sales_invoice, []).append(r)

# # 	tax_map = {}
# # 	for r in taxes:
# # 		tax_map.setdefault(r.sales_invoice, []).append(r)

# # 	data = []
# # 	for h in headers:
# # 		row = {
# # 			"voucher_type": "Sales Invoice",
# # 			"sales_invoice": h.sales_invoice,
# # 			"posting_date": h.posting_date,
# # 			"customer": h.customer,
# # 			"receivable_account": h.receivable_account,
# # 			"vat_emirate": h.vat_emirate,
# # 		}
# # 		for acc in income_accounts:
# # 			row[_account_fieldname(acc)] = 0
# # 		for acc in tax_accounts:
# # 			row[_account_fieldname(acc)] = 0

# # 		net_total = 0
# # 		for it in item_map.get(h.sales_invoice, []):
# # 			net_total += flt(it.base_net_amount)
# # 			if it.income_account:
# # 				row[_account_fieldname(it.income_account)] = flt(row[_account_fieldname(it.income_account)]) + flt(
# # 					it.base_net_amount
# # 				)

# # 		tax_total = 0
# # 		for t in tax_map.get(h.sales_invoice, []):
# # 			tax_total += flt(t.base_tax_amount)
# # 			if t.account_head:
# # 				row[_account_fieldname(t.account_head)] = flt(row[_account_fieldname(t.account_head)]) + flt(
# # 					t.base_tax_amount
# # 				)

# # 		row["net_total"] = flt(net_total)
# # 		row["tax_total"] = flt(tax_total)
# # 		row["grand_total"] = flt(net_total + tax_total)
# # 		data.append(row)

# # 	columns = _sales_breakdown_columns(income_accounts, tax_accounts)
# # 	return columns, data


# # def _sales_breakdown_columns(income_accounts, tax_accounts):
# # 	columns = [
# # 		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 110},
# # 		{
# # 			"fieldname": "sales_invoice",
# # 			"label": _("Sales Invoice No"),
# # 			"fieldtype": "Link",
# # 			"options": "Sales Invoice",
# # 			"width": 150,
# # 		},
# # 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# # 		{"fieldname": "vat_emirate", "label": _("VAT Emirates"), "fieldtype": "Data", "width": 140},
# # 		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 220},
# # 		{"fieldname": "receivable_account", "label": _("Receivable Account"), "fieldtype": "Data", "width": 220},
# # 	]
# # 	for acc in income_accounts:
# # 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# # 	for acc in tax_accounts:
# # 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# # 	columns.extend(
# # 		[
# # 			{"fieldname": "net_total", "label": _("Net Total"), "fieldtype": "Currency", "width": 140},
# # 			{"fieldname": "tax_total", "label": _("Tax Total"), "fieldtype": "Currency", "width": 140},
# # 			{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 150},
# # 		]
# # 	)
# # 	return columns


# # # ------------------------------------------------------------------
# # # Condition builders
# # # ------------------------------------------------------------------


# # def _si_conditions(company, from_date, to_date):
# # 	cond = "AND si.docstatus = 1"
# # 	params = []
# # 	if company:
# # 		cond += " AND si.company = %s"
# # 		params.append(company)
# # 	if from_date:
# # 		cond += " AND si.posting_date >= %s"
# # 		params.append(from_date)
# # 	if to_date:
# # 		cond += " AND si.posting_date <= %s"
# # 		params.append(to_date)
# # 	return cond, params


# # def _pi_conditions(company, from_date, to_date):
# # 	cond = "AND pi.docstatus = 1"
# # 	params = []
# # 	if company:
# # 		cond += " AND pi.company = %s"
# # 		params.append(company)
# # 	if from_date:
# # 		cond += " AND pi.posting_date >= %s"
# # 		params.append(from_date)
# # 	if to_date:
# # 		cond += " AND pi.posting_date <= %s"
# # 		params.append(to_date)
# # 	return cond, params


# # def _gl_conditions(company):
# # 	cond = "AND gl.docstatus = 1"
# # 	params = []
# # 	if company:
# # 		cond += " AND gl.account IN (SELECT account FROM `tabUAE VAT Account` WHERE parent = %s)"
# # 		params.append(company)
# # 	return cond, params


# # # ------------------------------------------------------------------
# # # Sales-side detail queries
# # # ------------------------------------------------------------------


# # def _rc_sales_detail(company, from_date, to_date):
# # 	cond, params = _pi_conditions(company, from_date, to_date)
# # 	gl_cond, gl_params = _gl_conditions(company)
# # 	cond += " AND pi.reverse_charge = 'Y' " + gl_cond
# # 	params.extend(gl_params)

# # 	return frappe.db.sql(
# # 		f"""
# # 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# # 		       pi.supplier_name AS party, '' AS item,
# # 		       pi.base_total AS amount, SUM(gl.debit) AS vat_amount
# # 		FROM `tabPurchase Invoice` pi
# # 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# # 		WHERE 1=1 {cond}
# # 		GROUP BY pi.name
# # 		ORDER BY pi.posting_date
# # 	""",
# # 		tuple(params),
# # 		as_dict=True,
# # 	)


# # # ------------------------------------------------------------------
# # # Purchase-side detail queries
# # # ------------------------------------------------------------------


# # def _std_expenses_detail(company, from_date, to_date):
# # 	cond, params = _pi_conditions(company, from_date, to_date)
# # 	cond += " AND pi.recoverable_standard_rated_expenses > 0"

# # 	return frappe.db.sql(
# # 		f"""
# # 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# # 		       pi.supplier_name AS party, '' AS item,
# # 		       pi.base_total AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
# # 		FROM `tabPurchase Invoice` pi
# # 		WHERE 1=1 {cond}
# # 		ORDER BY pi.posting_date
# # 	""",
# # 		tuple(params),
# # 		as_dict=True,
# # 	)


# # def _rc_expenses_detail(company, from_date, to_date):
# # 	cond, params = _pi_conditions(company, from_date, to_date)
# # 	gl_cond, gl_params = _gl_conditions(company)
# # 	cond += " AND pi.reverse_charge = 'Y' AND pi.recoverable_reverse_charge > 0 " + gl_cond
# # 	params.extend(gl_params)

# # 	return frappe.db.sql(
# # 		f"""
# # 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# # 		       pi.supplier_name AS party, '' AS item,
# # 		       pi.base_total AS amount,
# # 		       SUM(gl.debit * pi.recoverable_reverse_charge / 100) AS vat_amount
# # 		FROM `tabPurchase Invoice` pi
# # 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# # 		WHERE 1=1 {cond}
# # 		GROUP BY pi.name
# # 		ORDER BY pi.posting_date
# # 	""",
# # 		tuple(params),
# # 		as_dict=True,
# # 	)


# # # ------------------------------------------------------------------
# # # Combined detail queries
# # # ------------------------------------------------------------------


# # def _all_expenses_detail(company, from_date, to_date):
# # 	data = []
# # 	data.extend(_std_expenses_detail(company, from_date, to_date))
# # 	data.extend(_rc_expenses_detail(company, from_date, to_date))
# # 	return data


# # # ==================================================================
# # # Original helper functions
# # # ==================================================================


# # def get_total_emiratewise(filters):
# # 	conditions = get_conditions(filters)
# # 	try:
# # 		return frappe.db.sql(
# # 			f"""
# # 			select
# # 				s.vat_emirate as emirate, sum(i.base_net_amount) as total, sum(i.tax_amount)
# # 			from
# # 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# # 			on
# # 				i.parent = s.name
# # 			where
# # 				s.docstatus = 1 and i.is_exempt != 1 and i.is_zero_rated != 1
# # 				{conditions}
# # 			group by
# # 				s.vat_emirate;
# # 			""",
# # 			filters,
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_emirates():
# # 	return ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]


# # def get_filters(filters):
# # 	query_filters = []
# # 	if filters.get("company"):
# # 		query_filters.append(["company", "=", filters["company"]])
# # 	if filters.get("from_date"):
# # 		query_filters.append(["posting_date", ">=", filters["from_date"]])
# # 	if filters.get("from_date"):
# # 		query_filters.append(["posting_date", "<=", filters["to_date"]])
# # 	return query_filters


# # def get_reverse_charge_total(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["reverse_charge", "=", "Y"])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_reverse_charge_tax(filters):
# # 	conditions = get_conditions_join(filters)
# # 	return (
# # 		frappe.db.sql(
# # 			f"""
# # 		select sum(debit)  from
# # 			`tabPurchase Invoice` p inner join `tabGL Entry` gl
# # 		on
# # 			gl.voucher_no =  p.name
# # 		where
# # 			p.reverse_charge = "Y"
# # 			and p.docstatus = 1
# # 			and gl.docstatus = 1
# # 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# # 			{conditions} ;
# # 		""",
# # 			filters,
# # 		)[0][0]
# # 		or 0
# # 	)


# # def get_reverse_charge_recoverable_total(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["reverse_charge", "=", "Y"])
# # 	query_filters.append(["recoverable_reverse_charge", ">", "0"])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_reverse_charge_recoverable_tax(filters):
# # 	conditions = get_conditions_join(filters)
# # 	return (
# # 		frappe.db.sql(
# # 			f"""
# # 		select
# # 			sum(debit * p.recoverable_reverse_charge / 100)
# # 		from
# # 			`tabPurchase Invoice` p  inner join `tabGL Entry` gl
# # 		on
# # 			gl.voucher_no = p.name
# # 		where
# # 			p.reverse_charge = "Y"
# # 			and p.docstatus = 1
# # 			and p.recoverable_reverse_charge > 0
# # 			and gl.docstatus = 1
# # 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# # 			{conditions} ;
# # 		""",
# # 			filters,
# # 		)[0][0]
# # 		or 0
# # 	)


# # def get_conditions_join(filters):
# # 	conditions = ""
# # 	for opts in (
# # 		("company", " and p.company=%(company)s"),
# # 		("from_date", " and p.posting_date>=%(from_date)s"),
# # 		("to_date", " and p.posting_date<=%(to_date)s"),
# # 	):
# # 		if filters.get(opts[0]):
# # 			conditions += opts[1]
# # 	return conditions


# # def get_standard_rated_expenses_total(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_standard_rated_expenses_tax(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Purchase Invoice",
# # 				filters=query_filters,
# # 				fields=["sum(recoverable_standard_rated_expenses)"],
# # 				as_list=True,
# # 				limit=1,
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_tourist_tax_return_total(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["tourist_tax_return", ">", 0])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Sales Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_tourist_tax_return_tax(filters):
# # 	query_filters = get_filters(filters)
# # 	query_filters.append(["tourist_tax_return", ">", 0])
# # 	query_filters.append(["docstatus", "=", 1])
# # 	try:
# # 		return (
# # 			frappe.db.get_all(
# # 				"Sales Invoice",
# # 				filters=query_filters,
# # 				fields=["sum(tourist_tax_return)"],
# # 				as_list=True,
# # 				limit=1,
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_zero_rated_total(filters):
# # 	conditions = get_conditions(filters)
# # 	try:
# # 		return (
# # 			frappe.db.sql(
# # 				f"""
# # 			select
# # 				sum(i.base_net_amount) as total
# # 			from
# # 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# # 			on
# # 				i.parent = s.name
# # 			where
# # 				s.docstatus = 1 and  i.is_zero_rated = 1
# # 				{conditions} ;
# # 			""",
# # 				filters,
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_exempt_total(filters):
# # 	conditions = get_conditions(filters)
# # 	try:
# # 		return (
# # 			frappe.db.sql(
# # 				f"""
# # 			select
# # 				sum(i.base_net_amount) as total
# # 			from
# # 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# # 			on
# # 				i.parent = s.name
# # 			where
# # 				s.docstatus = 1 and  i.is_exempt = 1
# # 				{conditions} ;
# # 			""",
# # 				filters,
# # 			)[0][0]
# # 			or 0
# # 		)
# # 	except (IndexError, TypeError):
# # 		return 0


# # def get_conditions(filters):
# # 	conditions = ""
# # 	for opts in (
# # 		("company", " and company=%(company)s"),
# # 		("from_date", " and posting_date>=%(from_date)s"),
# # 		("to_date", " and posting_date<=%(to_date)s"),
# # 	):
# # 		if filters.get(opts[0]):
# # 			conditions += opts[1]
# # 	return conditions


# # # ==================================================================
# # # "See Transactions" review screen + automatic VAT Journal Entry
# # # ==================================================================

# # # Accounts used for the VAT Journal Entry (names taken from your Chart of Accounts).
# # # "VAT Receivable" does not exist yet: create it under Current Assets with exactly
# # # this name, or change the name here to match the account you create.
# # VAT_ACCOUNTS = {
# # 	"output_vat": "213000 - Output VAT - OIFM",
# # 	"output_vat_rcm": "213500 - Output VAT RCM - OIFM",
# # 	"input_vat": "118000 - Input VAT - OIFM",
# # 	"input_vat_rcm": "185000 - Input VAT RCM - OIFM",
# # 	"vat_payable": "218010 - VAT Payable - OIFM",
# # 	"vat_receivable": "118500 - VAT Receivable - OIFM",
# # }

# # # First line of the Journal Entry remark. Used to find which vouchers were already filed.
# # VAT_JE_MARKER = "UAE VAT 201 |"
# # VAT_SETTLE_MARKER = "UAE VAT 201 Settlement |"


# # def _all_vat_rows(company, from_date, to_date):
# # 	periods = (
# # 		("current", from_date, to_date),
# # 		("previous", add_months(from_date, -3), add_days(from_date, -1)),
# # 	)
# # 	rows = []
# # 	for section, start, end in periods:
# # 		for r in _collect_vat_transactions(company, start, end):
# # 			r["section"] = section
# # 			r["key"] = "{0}|{1}".format(r["category"], r["doc_name"])
# # 			rows.append(r)
# # 	return rows


# # def get_vat_transactions(filters):
# # 	"""All transactions behind the VAT 201 figures, for the filing period
# # 	(section 'current') and the three months before it (section 'previous')."""
# # 	company = filters.get("company")
# # 	rows = _all_vat_rows(company, getdate(filters.get("from_date")), getdate(filters.get("to_date")))

# # 	reported = _reported_vouchers(company)
# # 	for r in rows:
# # 		r["locked"] = r["doc_name"] in reported
# # 		if r["locked"]:
# # 			r["note"] = _("Already included in another return")
# # 		elif r["section"] == "previous":
# # 			r["note"] = _("Not previously reported")
# # 		else:
# # 			r["note"] = ""

# # 	columns = [
# # 		{"fieldname": "section", "label": _("Section"), "fieldtype": "Data", "width": 90},
# # 		{"fieldname": "doc_name", "label": _("Document No"), "fieldtype": "Data", "width": 160},
# # 		{"fieldname": "vat", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 140},
# # 	]
# # 	return columns, rows


# # def _collect_vat_transactions(company, start, end):
# # 	out = []

# # 	def add(doc_type, doc_name, posting_date, party, vtype, category, bucket, amount, vat):
# # 		out.append(
# # 			{
# # 				"doc_type": doc_type,
# # 				"doc_name": doc_name,
# # 				"posting_date": str(posting_date),
# # 				"party": party or "",
# # 				"type": vtype,  # Sales = output VAT, Purchase = input VAT
# # 				"category": category,
# # 				"bucket": bucket,  # which VAT account this belongs to
# # 				"amount": flt(amount),
# # 				"vat": flt(vat),
# # 			}
# # 		)

# # 	# Sales invoices (re-uses the existing breakdown query)
# # 	for category, kwargs in (
# # 		(_("Standard rated"), {}),
# # 		(_("Zero rated"), {"is_zero_rated": True}),
# # 		(_("Exempt"), {"is_exempt": True}),
# # 	):
# # 		_cols, data = _sales_invoice_breakdown(company, start, end, **kwargs)
# # 		for d in data:
# # 			vat = d["tax_total"] if not kwargs else 0
# # 			add("Sales Invoice", d["sales_invoice"], d["posting_date"], d["customer"],
# # 				"Sales", category, "output_vat", d["net_total"], vat)

# # 	# Tourist refunds (negative output VAT)
# # 	tourist_filters = [
# # 		["docstatus", "=", 1],
# # 		["posting_date", "between", [start, end]],
# # 		["tourist_tax_return", ">", 0],
# # 	]
# # 	if company:
# # 		tourist_filters.append(["company", "=", company])
# # 	for d in frappe.get_all(
# # 		"Sales Invoice",
# # 		filters=tourist_filters,
# # 		fields=["name", "posting_date", "customer_name", "base_total", "tourist_tax_return"],
# # 	):
# # 		add("Sales Invoice", d.name, d.posting_date, d.customer_name, "Sales",
# # 			_("Tourist refund"), "output_vat", -flt(d.base_total), -flt(d.tourist_tax_return))

# # 	# Reverse charge - output side
# # 	for d in _rc_sales_detail(company, start, end):
# # 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Sales",
# # 			_("Reverse charge (output)"), "output_vat_rcm", d.amount, d.vat_amount)

# # 	# Purchases - input side
# # 	for d in _std_expenses_detail(company, start, end):
# # 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# # 			_("Standard rated expense"), "input_vat", d.amount, d.vat_amount)

# # 	for d in _rc_expenses_detail(company, start, end):
# # 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# # 			_("Reverse charge (input)"), "input_vat_rcm", d.amount, d.vat_amount)

# # 	return sorted(out, key=lambda r: (r["posting_date"], r["doc_name"]))


# # def _reported_vouchers(company):
# # 	"""Voucher names already used in a VAT Journal Entry that is not cancelled.
# # 	They are read back from the 'Vouchers:' line in each entry's remark."""
# # 	remarks = frappe.get_all(
# # 		"Journal Entry",
# # 		filters={
# # 			"company": company,
# # 			"docstatus": ["<", 2],
# # 			"user_remark": ["like", VAT_JE_MARKER + "%"],
# # 		},
# # 		pluck="user_remark",
# # 	)
# # 	vouchers = set()
# # 	for remark in remarks:
# # 		for line in (remark or "").splitlines():
# # 			if line.startswith("Vouchers:"):
# # 				vouchers.update(v.strip() for v in line[len("Vouchers:") :].split(",") if v.strip())
# # 	return vouchers


# # def _build_vat_lines(totals):
# # 	"""Journal Entry lines that close the VAT accounts and move the net amount to
# # 	VAT Payable (output > input) or VAT Receivable (input > output)."""
# # 	lines = []
# # 	debit = credit = 0.0

# # 	for key in ("output_vat", "output_vat_rcm"):  # output VAT has a credit balance -> debit to clear
# # 		amt = flt(totals.get(key, 0), 2)
# # 		if amt > 0:
# # 			lines.append({"account": VAT_ACCOUNTS[key], "debit_in_account_currency": amt})
# # 			debit += amt
# # 		elif amt < 0:
# # 			lines.append({"account": VAT_ACCOUNTS[key], "credit_in_account_currency": -amt})
# # 			credit += -amt

# # 	for key in ("input_vat", "input_vat_rcm"):  # input VAT has a debit balance -> credit to clear
# # 		amt = flt(totals.get(key, 0), 2)
# # 		if amt > 0:
# # 			lines.append({"account": VAT_ACCOUNTS[key], "credit_in_account_currency": amt})
# # 			credit += amt
# # 		elif amt < 0:
# # 			lines.append({"account": VAT_ACCOUNTS[key], "debit_in_account_currency": -amt})
# # 			debit += -amt

# # 	net = flt(debit - credit, 2)
# # 	if net > 0:
# # 		lines.append({"account": VAT_ACCOUNTS["vat_payable"], "credit_in_account_currency": net})
# # 	elif net < 0:
# # 		lines.append({"account": VAT_ACCOUNTS["vat_receivable"], "debit_in_account_currency": -net})
# # 	return lines, net


# # def _check_accounts(accounts):
# # 	missing = [a for a in accounts if not frappe.db.exists("Account", a)]
# # 	if missing:
# # 		frappe.throw(
# # 			_("These accounts were not found: {0}. Create them (VAT Receivable goes under Current Assets) "
# # 			"or correct the names in VAT_ACCOUNTS in the report's Python file.").format(
# # 				", ".join(missing)
# # 			)
# # 		)


# # @frappe.whitelist()
# # def create_vat_journal_entry(company, from_date, to_date, keys):
# # 	"""Creates ONE draft Journal Entry for the selected transactions."""
# # 	frappe.has_permission("Journal Entry", "create", throw=True)
# # 	keys = json.loads(keys) if isinstance(keys, str) else keys
# # 	if not keys:
# # 		frappe.throw(_("Please select at least one transaction."))

# # 	from_date, to_date = getdate(from_date), getdate(to_date)
# # 	rows = {r["key"]: r for r in _all_vat_rows(company, from_date, to_date)}

# # 	selected = []
# # 	for k in keys:
# # 		if k not in rows:
# # 			frappe.throw(_("{0} is no longer available for this return. Please reload and select again.").format(k))
# # 		selected.append(rows[k])

# # 	reported = _reported_vouchers(company)
# # 	already = sorted({r["doc_name"] for r in selected if r["doc_name"] in reported})
# # 	if already:
# # 		frappe.throw(_("Already included in another return: {0}").format(", ".join(already)))

# # 	totals = {}
# # 	for r in selected:
# # 		totals[r["bucket"]] = totals.get(r["bucket"], 0) + r["vat"]

# # 	lines, net = _build_vat_lines(totals)
# # 	if not lines:
# # 		frappe.throw(_("The selected transactions have no VAT amount to post."))
# # 	_check_accounts([l["account"] for l in lines])

# # 	je = frappe.new_doc("Journal Entry")
# # 	je.voucher_type = "Journal Entry"
# # 	je.company = company
# # 	je.posting_date = to_date
# # 	je.user_remark = "{0} {1} | {2} to {3}\nVouchers: {4}".format(
# # 		VAT_JE_MARKER,
# # 		company,
# # 		from_date,
# # 		to_date,
# # 		", ".join(sorted({r["doc_name"] for r in selected})),
# # 	)
# # 	for l in lines:
# # 		je.append("accounts", l)
# # 	je.insert()  # stays in Draft so the accountant can review and submit

# # 	output = sum(flt(totals.get(k, 0)) for k in ("output_vat", "output_vat_rcm"))
# # 	inp = sum(flt(totals.get(k, 0)) for k in ("input_vat", "input_vat_rcm"))
# # 	return {
# # 		"name": je.name,
# # 		"output": flt(output, 2),
# # 		"input": flt(inp, 2),
# # 		"net": net,  # > 0 payable, < 0 receivable
# # 	}


# # @frappe.whitelist()
# # def create_vat_settlement_entry(journal_entry, bank_account, posting_date, reference_no, reference_date):
# # 	"""Payment of VAT Payable (Dr Payable, Cr Bank) or receipt of a VAT refund
# # 	(Dr Bank, Cr Receivable) as a draft Bank Entry."""
# # 	frappe.has_permission("Journal Entry", "create", throw=True)
# # 	src = frappe.get_doc("Journal Entry", journal_entry)
# # 	if not (src.user_remark or "").startswith(VAT_JE_MARKER) or src.docstatus == 2:
# # 		frappe.throw(_("{0} is not a valid VAT Journal Entry.").format(journal_entry))

# # 	marker = "{0} {1}".format(VAT_SETTLE_MARKER, src.name)
# # 	if frappe.db.exists(
# # 		"Journal Entry", {"docstatus": ["<", 2], "user_remark": ["like", marker + "%"]}
# # 	):
# # 		frappe.throw(_("A payment/refund entry already exists for {0}.").format(src.name))

# # 	if frappe.db.get_value("Account", bank_account, "company") != src.company:
# # 		frappe.throw(_("{0} does not belong to {1}.").format(bank_account, src.company))

# # 	payable = sum(
# # 		flt(r.credit_in_account_currency) - flt(r.debit_in_account_currency)
# # 		for r in src.accounts
# # 		if r.account == VAT_ACCOUNTS["vat_payable"]
# # 	)
# # 	receivable = sum(
# # 		flt(r.debit_in_account_currency) - flt(r.credit_in_account_currency)
# # 		for r in src.accounts
# # 		if r.account == VAT_ACCOUNTS["vat_receivable"]
# # 	)

# # 	if payable > 0:
# # 		amount = flt(payable, 2)
# # 		lines = [
# # 			{"account": VAT_ACCOUNTS["vat_payable"], "debit_in_account_currency": amount},
# # 			{"account": bank_account, "credit_in_account_currency": amount},
# # 		]
# # 	elif receivable > 0:
# # 		amount = flt(receivable, 2)
# # 		lines = [
# # 			{"account": bank_account, "debit_in_account_currency": amount},
# # 			{"account": VAT_ACCOUNTS["vat_receivable"], "credit_in_account_currency": amount},
# # 		]
# # 	else:
# # 		frappe.throw(_("There is no VAT payable or receivable to settle in {0}.").format(src.name))

# # 	je = frappe.new_doc("Journal Entry")
# # 	je.voucher_type = "Bank Entry"
# # 	je.company = src.company
# # 	je.posting_date = getdate(posting_date)
# # 	je.cheque_no = reference_no
# # 	je.cheque_date = getdate(reference_date)
# # 	je.user_remark = "{0}\nVAT payment/refund for {1}".format(marker, src.name)
# # 	for l in lines:
# # 		je.append("accounts", l)
# # 	je.insert()
# # 	return je.name



# # ////////////////////////////////////////////////

# ////////////////////////////////////////////////


# # Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# # For license information, please see license.txt


# import re

# import frappe
# from frappe import _
# from frappe.utils import flt


# def execute(filters=None):
# 	filters = filters or {}
# 	if filters.get("drilldown_key"):
# 		return get_drilldown(filters)
# 	columns = get_columns()
# 	data, emirates, amounts_by_emirate = get_data(filters)
# 	return columns, data


# # ------------------------------------------------------------------
# # Summary columns
# # ------------------------------------------------------------------


# def get_columns():
# 	return [
# 		{"fieldname": "no", "label": _("No"), "fieldtype": "Data", "width": 50},
# 		{"fieldname": "legend", "label": _("Legend"), "fieldtype": "Data", "width": 300},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 125},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# # ------------------------------------------------------------------
# # Summary data
# # ------------------------------------------------------------------


# def get_data(filters=None):
# 	data = []
# 	emirates, amounts_by_emirate = append_vat_on_sales(data, filters)
# 	append_vat_on_expenses(data, filters)
# 	return data, emirates, amounts_by_emirate


# def append_vat_on_sales(data, filters):
# 	append_data(data, "", _("VAT on Sales and All Other Outputs"), "", "")

# 	emirates, amounts_by_emirate = standard_rated_expenses_emiratewise(data, filters)

# 	total_amounts = [amounts_by_emirate.get(e, {}).get("raw_amount", 0) for e in emirates]
# 	total_vat_amounts = [amounts_by_emirate.get(e, {}).get("raw_vat_amount", 0) for e in emirates]

# 	tourist_total = get_tourist_tax_return_total(filters)
# 	tourist_tax = get_tourist_tax_return_tax(filters)
# 	append_data(
# 		data,
# 		"2",
# 		_("Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme"),
# 		frappe.format((-1) * tourist_total, "Currency"),
# 		frappe.format((-1) * tourist_tax, "Currency"),
# 		drilldown_key="tourist_refund",
# 		raw_amount=(-1) * tourist_total,
# 		raw_vat_amount=(-1) * tourist_tax,
# 	)
# 	total_amounts.append((-1) * tourist_total)
# 	total_vat_amounts.append((-1) * tourist_tax)

# 	rc_total = get_reverse_charge_total(filters)
# 	rc_tax = get_reverse_charge_tax(filters)
# 	append_data(
# 		data,
# 		"3",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_total, "Currency"),
# 		frappe.format(rc_tax, "Currency"),
# 		drilldown_key="reverse_charge_sales",
# 		raw_amount=rc_total,
# 		raw_vat_amount=rc_tax,
# 	)
# 	total_amounts.append(rc_total)
# 	total_vat_amounts.append(rc_tax)

# 	zero_total = get_zero_rated_total(filters)
# 	append_data(
# 		data,
# 		"4",
# 		_("Zero Rated"),
# 		frappe.format(zero_total, "Currency"),
# 		"-",
# 		drilldown_key="zero_rated",
# 		raw_amount=zero_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(zero_total)

# 	exempt_total = get_exempt_total(filters)
# 	append_data(
# 		data,
# 		"5",
# 		_("Exempt Supplies"),
# 		frappe.format(exempt_total, "Currency"),
# 		"-",
# 		drilldown_key="exempt",
# 		raw_amount=exempt_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(exempt_total)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Sales and All Other Outputs"),
# 		frappe.format(sum(total_amounts), "Currency"),
# 		frappe.format(sum(total_vat_amounts), "Currency"),
# 	)

# 	append_data(data, "", "", "", "")

# 	return emirates, amounts_by_emirate


# def standard_rated_expenses_emiratewise(data, filters):
# 	total_emiratewise = get_total_emiratewise(filters)
# 	emirates = get_emirates()
# 	amounts_by_emirate = {}
# 	for emirate, amount, vat in total_emiratewise:
# 		amounts_by_emirate[emirate] = {
# 			"legend": emirate,
# 			"raw_amount": flt(amount),
# 			"raw_vat_amount": flt(vat),
# 			"amount": frappe.format(amount, "Currency"),
# 			"vat_amount": frappe.format(vat, "Currency"),
# 		}
# 	amounts_by_emirate = append_emiratewise_expenses(data, emirates, amounts_by_emirate)
# 	return emirates, amounts_by_emirate


# def append_emiratewise_expenses(data, emirates, amounts_by_emirate):
# 	for no, emirate in enumerate(emirates, 97):
# 		key = "standard_rated_{0}".format(emirate)
# 		if emirate in amounts_by_emirate:
# 			amounts_by_emirate[emirate]["no"] = _("1{0}").format(chr(no))
# 			amounts_by_emirate[emirate]["legend"] = _("Standard rated supplies in {0}").format(emirate)
# 			amounts_by_emirate[emirate]["drilldown_key"] = key
# 			data.append(amounts_by_emirate[emirate])
# 		else:
# 			append_data(
# 				data,
# 				_("1{0}").format(chr(no)),
# 				_("Standard rated supplies in {0}").format(emirate),
# 				frappe.format(0, "Currency"),
# 				frappe.format(0, "Currency"),
# 				drilldown_key=key,
# 				raw_amount=0,
# 				raw_vat_amount=0,
# 			)
# 	return amounts_by_emirate


# def append_vat_on_expenses(data, filters):
# 	append_data(data, "", _("VAT on Expenses and All Other Inputs"), "", "")

# 	std_exp_total = get_standard_rated_expenses_total(filters)
# 	std_exp_tax = get_standard_rated_expenses_tax(filters)
# 	append_data(
# 		data,
# 		"9",
# 		_("Standard Rated Expenses"),
# 		frappe.format(std_exp_total, "Currency"),
# 		frappe.format(std_exp_tax, "Currency"),
# 		drilldown_key="standard_rated_expenses",
# 		raw_amount=std_exp_total,
# 		raw_vat_amount=std_exp_tax,
# 	)

# 	rc_rec_total = get_reverse_charge_recoverable_total(filters)
# 	rc_rec_tax = get_reverse_charge_recoverable_tax(filters)
# 	append_data(
# 		data,
# 		"10",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_rec_total, "Currency"),
# 		frappe.format(rc_rec_tax, "Currency"),
# 		drilldown_key="reverse_charge_expenses",
# 		raw_amount=rc_rec_total,
# 		raw_vat_amount=rc_rec_tax,
# 	)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Expenses and All Other Inputs"),
# 		frappe.format(std_exp_total + rc_rec_total, "Currency"),
# 		frappe.format(std_exp_tax + rc_rec_tax, "Currency"),
# 	)


# def append_data(data, no, legend, amount, vat_amount, drilldown_key=None, raw_amount=0, raw_vat_amount=0):
# 	row = {"no": no, "legend": legend, "amount": amount, "vat_amount": vat_amount}
# 	if drilldown_key:
# 		row["drilldown_key"] = drilldown_key
# 		row["raw_amount"] = raw_amount
# 		row["raw_vat_amount"] = raw_vat_amount
# 	data.append(row)


# # ==================================================================
# # Drill-down
# # ==================================================================


# def get_drilldown(filters):
# 	key = filters.get("drilldown_key")
# 	company = filters.get("company")
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")

# 	purchase_keys = ("standard_rated_expenses", "reverse_charge_expenses", "expenses_total")
# 	if key in purchase_keys:
# 		columns, data = _get_purchase_detail(key, company, from_date, to_date)
# 	elif key == "reverse_charge_sales":
# 		columns = _purchase_detail_columns()
# 		data = _rc_sales_detail(company, from_date, to_date)
# 	else:
# 		columns, data = _get_sales_detail(key, company, from_date, to_date)

# 	return columns, data, None, None, None, True


# def _get_sales_detail(key, company, from_date, to_date):
# 	if key.startswith("standard_rated_"):
# 		emirate = key[len("standard_rated_") :]
# 		return _sales_invoice_breakdown(company, from_date, to_date, emirate=emirate)
# 	elif key == "tourist_refund":
# 		return _sales_invoice_breakdown(company, from_date, to_date, tourist_only=True)
# 	elif key == "zero_rated":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_zero_rated=True)
# 	elif key == "exempt":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_exempt=True)
# 	elif key == "sales_total":
# 		return _sales_invoice_breakdown(company, from_date, to_date)
# 	return [], []


# def _get_purchase_detail(key, company, from_date, to_date):
# 	columns = _purchase_detail_columns()
# 	if key == "standard_rated_expenses":
# 		data = _std_expenses_detail(company, from_date, to_date)
# 	elif key == "reverse_charge_expenses":
# 		data = _rc_expenses_detail(company, from_date, to_date)
# 	elif key == "expenses_total":
# 		data = _all_expenses_detail(company, from_date, to_date)
# 	else:
# 		data = []
# 	return columns, data


# def _purchase_detail_columns():
# 	return [
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{
# 			"fieldname": "doc_name",
# 			"label": _("Document No"),
# 			"fieldtype": "Dynamic Link",
# 			"options": "doc_type",
# 			"width": 180,
# 		},
# 		{"fieldname": "party", "label": _("Party"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "item", "label": _("Item"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 130},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# def _account_fieldname(account):
# 	"""Sanitize an account name for use as a column fieldname."""
# 	return "acc_" + re.sub(r"[^a-zA-Z0-9_]", "_", account)


# def _sales_invoice_breakdown(
# 	company, from_date, to_date, emirate=None, is_zero_rated=False, is_exempt=False, tourist_only=False
# ):
# 	"""Account-wise breakdown of qualifying Sales Invoices."""
# 	si_cond, si_params = _si_conditions(company, from_date, to_date)

# 	if tourist_only:
# 		invoices = frappe.db.sql_list(
# 			"SELECT si.name FROM `tabSales Invoice` si WHERE 1=1 "
# 			+ si_cond + " AND si.tourist_tax_return > 0",
# 			tuple(si_params),
# 		)
# 	else:
# 		item_cond = ""
# 		item_params = []
# 		if emirate:
# 			item_cond += " AND si.vat_emirate = %s"
# 			item_params.append(emirate)
# 		if is_zero_rated:
# 			item_cond += " AND sii.is_zero_rated = 1"
# 		elif is_exempt:
# 			item_cond += " AND sii.is_exempt = 1"
# 		else:
# 			item_cond += " AND sii.is_exempt != 1 AND sii.is_zero_rated != 1"

# 		invoices = frappe.db.sql_list(
# 			"SELECT DISTINCT si.name FROM `tabSales Invoice Item` sii "
# 			"INNER JOIN `tabSales Invoice` si ON si.name = sii.parent "
# 			"WHERE 1=1 " + si_cond + item_cond,
# 			tuple(si_params + item_params),
# 		)

# 	if not invoices:
# 		return _sales_breakdown_columns([], []), []

# 	invoices_tuple = tuple(invoices)

# 	headers = frappe.db.sql(
# 		"""
# 		SELECT si.name AS sales_invoice, si.posting_date, si.customer_name AS customer,
# 		       si.debit_to AS receivable_account, si.vat_emirate
# 		FROM `tabSales Invoice` si
# 		WHERE si.docstatus = 1 AND si.name IN %s
# 		ORDER BY si.posting_date
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	items = frappe.db.sql(
# 		"""
# 		SELECT sii.parent AS sales_invoice, sii.income_account, sii.base_net_amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# 		WHERE si.docstatus = 1 AND sii.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	taxes = frappe.db.sql(
# 		"""
# 		SELECT stc.parent AS sales_invoice, stc.account_head, stc.base_tax_amount
# 		FROM `tabSales Taxes and Charges` stc
# 		INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
# 		WHERE si.docstatus = 1 AND stc.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	income_accounts = sorted({r.income_account for r in items if r.income_account})
# 	tax_accounts = sorted({r.account_head for r in taxes if r.account_head})

# 	item_map = {}
# 	for r in items:
# 		item_map.setdefault(r.sales_invoice, []).append(r)

# 	tax_map = {}
# 	for r in taxes:
# 		tax_map.setdefault(r.sales_invoice, []).append(r)

# 	data = []
# 	for h in headers:
# 		row = {
# 			"voucher_type": "Sales Invoice",
# 			"sales_invoice": h.sales_invoice,
# 			"posting_date": h.posting_date,
# 			"customer": h.customer,
# 			"receivable_account": h.receivable_account,
# 			"vat_emirate": h.vat_emirate,
# 		}
# 		for acc in income_accounts:
# 			row[_account_fieldname(acc)] = 0
# 		for acc in tax_accounts:
# 			row[_account_fieldname(acc)] = 0

# 		net_total = 0
# 		for it in item_map.get(h.sales_invoice, []):
# 			net_total += flt(it.base_net_amount)
# 			if it.income_account:
# 				row[_account_fieldname(it.income_account)] = flt(row[_account_fieldname(it.income_account)]) + flt(
# 					it.base_net_amount
# 				)

# 		tax_total = 0
# 		for t in tax_map.get(h.sales_invoice, []):
# 			tax_total += flt(t.base_tax_amount)
# 			if t.account_head:
# 				row[_account_fieldname(t.account_head)] = flt(row[_account_fieldname(t.account_head)]) + flt(
# 					t.base_tax_amount
# 				)

# 		row["net_total"] = flt(net_total)
# 		row["tax_total"] = flt(tax_total)
# 		row["grand_total"] = flt(net_total + tax_total)
# 		data.append(row)

# 	columns = _sales_breakdown_columns(income_accounts, tax_accounts)
# 	return columns, data


# def _sales_breakdown_columns(income_accounts, tax_accounts):
# 	columns = [
# 		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 110},
# 		{
# 			"fieldname": "sales_invoice",
# 			"label": _("Sales Invoice No"),
# 			"fieldtype": "Link",
# 			"options": "Sales Invoice",
# 			"width": 150,
# 		},
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{"fieldname": "vat_emirate", "label": _("VAT Emirates"), "fieldtype": "Data", "width": 140},
# 		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 220},
# 		{"fieldname": "receivable_account", "label": _("Receivable Account"), "fieldtype": "Data", "width": 220},
# 	]
# 	for acc in income_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	for acc in tax_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	columns.extend(
# 		[
# 			{"fieldname": "net_total", "label": _("Net Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "tax_total", "label": _("Tax Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 150},
# 		]
# 	)
# 	return columns


# # ------------------------------------------------------------------
# # Condition builders
# # ------------------------------------------------------------------


# def _si_conditions(company, from_date, to_date):
# 	cond = "AND si.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND si.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND si.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND si.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _pi_conditions(company, from_date, to_date):
# 	cond = "AND pi.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND pi.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND pi.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND pi.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _gl_conditions(company):
# 	cond = "AND gl.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND gl.account IN (SELECT account FROM `tabUAE VAT Account` WHERE parent = %s)"
# 		params.append(company)
# 	return cond, params


# # ------------------------------------------------------------------
# # Sales-side detail queries
# # ------------------------------------------------------------------


# def _rc_sales_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, SUM(gl.debit) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Purchase-side detail queries
# # ------------------------------------------------------------------


# def _std_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	cond += " AND pi.recoverable_standard_rated_expenses > 0"

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		WHERE 1=1 {cond}
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# def _rc_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' AND pi.recoverable_reverse_charge > 0 " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount,
# 		       SUM(gl.debit * pi.recoverable_reverse_charge / 100) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Combined detail queries
# # ------------------------------------------------------------------


# def _all_expenses_detail(company, from_date, to_date):
# 	data = []
# 	data.extend(_std_expenses_detail(company, from_date, to_date))
# 	data.extend(_rc_expenses_detail(company, from_date, to_date))
# 	return data


# # ==================================================================
# # Original helper functions
# # ==================================================================


# def get_total_emiratewise(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return frappe.db.sql(
# 			f"""
# 			select
# 				s.vat_emirate as emirate, sum(i.base_net_amount) as total, sum(i.tax_amount)
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and i.is_exempt != 1 and i.is_zero_rated != 1
# 				{conditions}
# 			group by
# 				s.vat_emirate;
# 			""",
# 			filters,
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_emirates():
# 	return ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]


# def get_filters(filters):
# 	query_filters = []
# 	if filters.get("company"):
# 		query_filters.append(["company", "=", filters["company"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", ">=", filters["from_date"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", "<=", filters["to_date"]])
# 	return query_filters


# def get_reverse_charge_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select sum(debit)  from
# 			`tabPurchase Invoice` p inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no =  p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_reverse_charge_recoverable_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["recoverable_reverse_charge", ">", "0"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_recoverable_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select
# 			sum(debit * p.recoverable_reverse_charge / 100)
# 		from
# 			`tabPurchase Invoice` p  inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no = p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and p.recoverable_reverse_charge > 0
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_conditions_join(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and p.company=%(company)s"),
# 		("from_date", " and p.posting_date>=%(from_date)s"),
# 		("to_date", " and p.posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# def get_standard_rated_expenses_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_standard_rated_expenses_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice",
# 				filters=query_filters,
# 				fields=["sum(recoverable_standard_rated_expenses)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice",
# 				filters=query_filters,
# 				fields=["sum(tourist_tax_return)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_zero_rated_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_zero_rated = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_exempt_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_exempt = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_conditions(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and company=%(company)s"),
# 		("from_date", " and posting_date>=%(from_date)s"),
# 		("to_date", " and posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


# import json
# import re

# import frappe
# from frappe import _
# from frappe.utils import add_days, add_months, flt, getdate


# def execute(filters=None):
# 	filters = filters or {}
# 	if not filters.get("company"):  # first page load runs the report with empty filters
# 		return get_columns(), []
# 	if filters.get("drilldown_key") == "vat_transactions":
# 		return get_vat_transactions(filters)
# 	if filters.get("drilldown_key"):
# 		return get_drilldown(filters)
# 	columns = get_columns()
# 	data, emirates, amounts_by_emirate = get_data(filters)
# 	return columns, data


# # ------------------------------------------------------------------
# # Summary columns
# # ------------------------------------------------------------------


# def get_columns():
# 	return [
# 		{"fieldname": "no", "label": _("No"), "fieldtype": "Data", "width": 50},
# 		{"fieldname": "legend", "label": _("Legend"), "fieldtype": "Data", "width": 300},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 125},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# # ------------------------------------------------------------------
# # Summary data
# # ------------------------------------------------------------------


# def get_data(filters=None):
# 	data = []
# 	emirates, amounts_by_emirate = append_vat_on_sales(data, filters)
# 	append_vat_on_expenses(data, filters)
# 	return data, emirates, amounts_by_emirate


# def append_vat_on_sales(data, filters):
# 	append_data(data, "", _("VAT on Sales and All Other Outputs"), "", "")

# 	emirates, amounts_by_emirate = standard_rated_expenses_emiratewise(data, filters)

# 	total_amounts = [amounts_by_emirate.get(e, {}).get("raw_amount", 0) for e in emirates]
# 	total_vat_amounts = [amounts_by_emirate.get(e, {}).get("raw_vat_amount", 0) for e in emirates]

# 	tourist_total = get_tourist_tax_return_total(filters)
# 	tourist_tax = get_tourist_tax_return_tax(filters)
# 	append_data(
# 		data,
# 		"2",
# 		_("Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme"),
# 		frappe.format((-1) * tourist_total, "Currency"),
# 		frappe.format((-1) * tourist_tax, "Currency"),
# 		drilldown_key="tourist_refund",
# 		raw_amount=(-1) * tourist_total,
# 		raw_vat_amount=(-1) * tourist_tax,
# 	)
# 	total_amounts.append((-1) * tourist_total)
# 	total_vat_amounts.append((-1) * tourist_tax)

# 	rc_total = get_reverse_charge_total(filters)
# 	rc_tax = get_reverse_charge_tax(filters)
# 	append_data(
# 		data,
# 		"3",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_total, "Currency"),
# 		frappe.format(rc_tax, "Currency"),
# 		drilldown_key="reverse_charge_sales",
# 		raw_amount=rc_total,
# 		raw_vat_amount=rc_tax,
# 	)
# 	total_amounts.append(rc_total)
# 	total_vat_amounts.append(rc_tax)

# 	zero_total = get_zero_rated_total(filters)
# 	append_data(
# 		data,
# 		"4",
# 		_("Zero Rated"),
# 		frappe.format(zero_total, "Currency"),
# 		"-",
# 		drilldown_key="zero_rated",
# 		raw_amount=zero_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(zero_total)

# 	exempt_total = get_exempt_total(filters)
# 	append_data(
# 		data,
# 		"5",
# 		_("Exempt Supplies"),
# 		frappe.format(exempt_total, "Currency"),
# 		"-",
# 		drilldown_key="exempt",
# 		raw_amount=exempt_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(exempt_total)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Sales and All Other Outputs"),
# 		frappe.format(sum(total_amounts), "Currency"),
# 		frappe.format(sum(total_vat_amounts), "Currency"),
# 	)

# 	append_data(data, "", "", "", "")

# 	return emirates, amounts_by_emirate


# def standard_rated_expenses_emiratewise(data, filters):
# 	total_emiratewise = get_total_emiratewise(filters)
# 	emirates = get_emirates()
# 	amounts_by_emirate = {}
# 	for emirate, amount, vat in total_emiratewise:
# 		amounts_by_emirate[emirate] = {
# 			"legend": emirate,
# 			"raw_amount": flt(amount),
# 			"raw_vat_amount": flt(vat),
# 			"amount": frappe.format(amount, "Currency"),
# 			"vat_amount": frappe.format(vat, "Currency"),
# 		}
# 	amounts_by_emirate = append_emiratewise_expenses(data, emirates, amounts_by_emirate)
# 	return emirates, amounts_by_emirate


# def append_emiratewise_expenses(data, emirates, amounts_by_emirate):
# 	for no, emirate in enumerate(emirates, 97):
# 		key = "standard_rated_{0}".format(emirate)
# 		if emirate in amounts_by_emirate:
# 			amounts_by_emirate[emirate]["no"] = _("1{0}").format(chr(no))
# 			amounts_by_emirate[emirate]["legend"] = _("Standard rated supplies in {0}").format(emirate)
# 			amounts_by_emirate[emirate]["drilldown_key"] = key
# 			data.append(amounts_by_emirate[emirate])
# 		else:
# 			append_data(
# 				data,
# 				_("1{0}").format(chr(no)),
# 				_("Standard rated supplies in {0}").format(emirate),
# 				frappe.format(0, "Currency"),
# 				frappe.format(0, "Currency"),
# 				drilldown_key=key,
# 				raw_amount=0,
# 				raw_vat_amount=0,
# 			)
# 	return amounts_by_emirate


# def append_vat_on_expenses(data, filters):
# 	append_data(data, "", _("VAT on Expenses and All Other Inputs"), "", "")

# 	std_exp_total = get_standard_rated_expenses_total(filters)
# 	std_exp_tax = get_standard_rated_expenses_tax(filters)
# 	append_data(
# 		data,
# 		"9",
# 		_("Standard Rated Expenses"),
# 		frappe.format(std_exp_total, "Currency"),
# 		frappe.format(std_exp_tax, "Currency"),
# 		drilldown_key="standard_rated_expenses",
# 		raw_amount=std_exp_total,
# 		raw_vat_amount=std_exp_tax,
# 	)

# 	rc_rec_total = get_reverse_charge_recoverable_total(filters)
# 	rc_rec_tax = get_reverse_charge_recoverable_tax(filters)
# 	append_data(
# 		data,
# 		"10",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_rec_total, "Currency"),
# 		frappe.format(rc_rec_tax, "Currency"),
# 		drilldown_key="reverse_charge_expenses",
# 		raw_amount=rc_rec_total,
# 		raw_vat_amount=rc_rec_tax,
# 	)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Expenses and All Other Inputs"),
# 		frappe.format(std_exp_total + rc_rec_total, "Currency"),
# 		frappe.format(std_exp_tax + rc_rec_tax, "Currency"),
# 	)


# def append_data(data, no, legend, amount, vat_amount, drilldown_key=None, raw_amount=0, raw_vat_amount=0):
# 	row = {"no": no, "legend": legend, "amount": amount, "vat_amount": vat_amount}
# 	if drilldown_key:
# 		row["drilldown_key"] = drilldown_key
# 		row["raw_amount"] = raw_amount
# 		row["raw_vat_amount"] = raw_vat_amount
# 	data.append(row)


# # ==================================================================
# # Drill-down
# # ==================================================================


# def get_drilldown(filters):
# 	key = filters.get("drilldown_key")
# 	company = filters.get("company")
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")

# 	purchase_keys = ("standard_rated_expenses", "reverse_charge_expenses", "expenses_total")
# 	if key in purchase_keys:
# 		columns, data = _get_purchase_detail(key, company, from_date, to_date)
# 	elif key == "reverse_charge_sales":
# 		columns = _purchase_detail_columns()
# 		data = _rc_sales_detail(company, from_date, to_date)
# 	else:
# 		columns, data = _get_sales_detail(key, company, from_date, to_date)

# 	return columns, data, None, None, None, True


# def _get_sales_detail(key, company, from_date, to_date):
# 	if key.startswith("standard_rated_"):
# 		emirate = key[len("standard_rated_") :]
# 		return _sales_invoice_breakdown(company, from_date, to_date, emirate=emirate)
# 	elif key == "tourist_refund":
# 		return _sales_invoice_breakdown(company, from_date, to_date, tourist_only=True)
# 	elif key == "zero_rated":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_zero_rated=True)
# 	elif key == "exempt":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_exempt=True)
# 	elif key == "sales_total":
# 		return _sales_invoice_breakdown(company, from_date, to_date)
# 	return [], []


# def _get_purchase_detail(key, company, from_date, to_date):
# 	columns = _purchase_detail_columns()
# 	if key == "standard_rated_expenses":
# 		data = _std_expenses_detail(company, from_date, to_date)
# 	elif key == "reverse_charge_expenses":
# 		data = _rc_expenses_detail(company, from_date, to_date)
# 	elif key == "expenses_total":
# 		data = _all_expenses_detail(company, from_date, to_date)
# 	else:
# 		data = []
# 	return columns, data


# def _purchase_detail_columns():
# 	return [
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{
# 			"fieldname": "doc_name",
# 			"label": _("Document No"),
# 			"fieldtype": "Dynamic Link",
# 			"options": "doc_type",
# 			"width": 180,
# 		},
# 		{"fieldname": "party", "label": _("Party"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "item", "label": _("Item"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 130},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# def _account_fieldname(account):
# 	"""Sanitize an account name for use as a column fieldname."""
# 	return "acc_" + re.sub(r"[^a-zA-Z0-9_]", "_", account)


# def _sales_invoice_breakdown(
# 	company, from_date, to_date, emirate=None, is_zero_rated=False, is_exempt=False, tourist_only=False
# ):
# 	"""Account-wise breakdown of qualifying Sales Invoices."""
# 	si_cond, si_params = _si_conditions(company, from_date, to_date)

# 	if tourist_only:
# 		invoices = frappe.db.sql_list(
# 			"SELECT si.name FROM `tabSales Invoice` si WHERE 1=1 "
# 			+ si_cond + " AND si.tourist_tax_return > 0",
# 			tuple(si_params),
# 		)
# 	else:
# 		item_cond = ""
# 		item_params = []
# 		if emirate:
# 			item_cond += " AND si.vat_emirate = %s"
# 			item_params.append(emirate)
# 		if is_zero_rated:
# 			item_cond += " AND sii.is_zero_rated = 1"
# 		elif is_exempt:
# 			item_cond += " AND sii.is_exempt = 1"
# 		else:
# 			item_cond += " AND sii.is_exempt != 1 AND sii.is_zero_rated != 1"

# 		invoices = frappe.db.sql_list(
# 			"SELECT DISTINCT si.name FROM `tabSales Invoice Item` sii "
# 			"INNER JOIN `tabSales Invoice` si ON si.name = sii.parent "
# 			"WHERE 1=1 " + si_cond + item_cond,
# 			tuple(si_params + item_params),
# 		)

# 	if not invoices:
# 		return _sales_breakdown_columns([], []), []

# 	invoices_tuple = tuple(invoices)

# 	headers = frappe.db.sql(
# 		"""
# 		SELECT si.name AS sales_invoice, si.posting_date, si.customer_name AS customer,
# 		       si.debit_to AS receivable_account, si.vat_emirate
# 		FROM `tabSales Invoice` si
# 		WHERE si.docstatus = 1 AND si.name IN %s
# 		ORDER BY si.posting_date
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	items = frappe.db.sql(
# 		"""
# 		SELECT sii.parent AS sales_invoice, sii.income_account, sii.base_net_amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# 		WHERE si.docstatus = 1 AND sii.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	taxes = frappe.db.sql(
# 		"""
# 		SELECT stc.parent AS sales_invoice, stc.account_head, stc.base_tax_amount
# 		FROM `tabSales Taxes and Charges` stc
# 		INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
# 		WHERE si.docstatus = 1 AND stc.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	income_accounts = sorted({r.income_account for r in items if r.income_account})
# 	tax_accounts = sorted({r.account_head for r in taxes if r.account_head})

# 	item_map = {}
# 	for r in items:
# 		item_map.setdefault(r.sales_invoice, []).append(r)

# 	tax_map = {}
# 	for r in taxes:
# 		tax_map.setdefault(r.sales_invoice, []).append(r)

# 	data = []
# 	for h in headers:
# 		row = {
# 			"voucher_type": "Sales Invoice",
# 			"sales_invoice": h.sales_invoice,
# 			"posting_date": h.posting_date,
# 			"customer": h.customer,
# 			"receivable_account": h.receivable_account,
# 			"vat_emirate": h.vat_emirate,
# 		}
# 		for acc in income_accounts:
# 			row[_account_fieldname(acc)] = 0
# 		for acc in tax_accounts:
# 			row[_account_fieldname(acc)] = 0

# 		net_total = 0
# 		for it in item_map.get(h.sales_invoice, []):
# 			net_total += flt(it.base_net_amount)
# 			if it.income_account:
# 				row[_account_fieldname(it.income_account)] = flt(row[_account_fieldname(it.income_account)]) + flt(
# 					it.base_net_amount
# 				)

# 		tax_total = 0
# 		for t in tax_map.get(h.sales_invoice, []):
# 			tax_total += flt(t.base_tax_amount)
# 			if t.account_head:
# 				row[_account_fieldname(t.account_head)] = flt(row[_account_fieldname(t.account_head)]) + flt(
# 					t.base_tax_amount
# 				)

# 		row["net_total"] = flt(net_total)
# 		row["tax_total"] = flt(tax_total)
# 		row["grand_total"] = flt(net_total + tax_total)
# 		data.append(row)

# 	columns = _sales_breakdown_columns(income_accounts, tax_accounts)
# 	return columns, data


# def _sales_breakdown_columns(income_accounts, tax_accounts):
# 	columns = [
# 		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 110},
# 		{
# 			"fieldname": "sales_invoice",
# 			"label": _("Sales Invoice No"),
# 			"fieldtype": "Link",
# 			"options": "Sales Invoice",
# 			"width": 150,
# 		},
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{"fieldname": "vat_emirate", "label": _("VAT Emirates"), "fieldtype": "Data", "width": 140},
# 		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 220},
# 		{"fieldname": "receivable_account", "label": _("Receivable Account"), "fieldtype": "Data", "width": 220},
# 	]
# 	for acc in income_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	for acc in tax_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	columns.extend(
# 		[
# 			{"fieldname": "net_total", "label": _("Net Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "tax_total", "label": _("Tax Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 150},
# 		]
# 	)
# 	return columns


# # ------------------------------------------------------------------
# # Condition builders
# # ------------------------------------------------------------------


# def _si_conditions(company, from_date, to_date):
# 	cond = "AND si.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND si.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND si.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND si.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _pi_conditions(company, from_date, to_date):
# 	cond = "AND pi.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND pi.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND pi.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND pi.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _gl_conditions(company):
# 	cond = "AND gl.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND gl.account IN (SELECT account FROM `tabUAE VAT Account` WHERE parent = %s)"
# 		params.append(company)
# 	return cond, params


# # ------------------------------------------------------------------
# # Sales-side detail queries
# # ------------------------------------------------------------------


# def _rc_sales_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, SUM(gl.debit) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Purchase-side detail queries
# # ------------------------------------------------------------------


# def _std_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	cond += " AND pi.recoverable_standard_rated_expenses > 0"

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		WHERE 1=1 {cond}
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# def _rc_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' AND pi.recoverable_reverse_charge > 0 " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount,
# 		       SUM(gl.debit * pi.recoverable_reverse_charge / 100) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Combined detail queries
# # ------------------------------------------------------------------


# def _all_expenses_detail(company, from_date, to_date):
# 	data = []
# 	data.extend(_std_expenses_detail(company, from_date, to_date))
# 	data.extend(_rc_expenses_detail(company, from_date, to_date))
# 	return data


# # ==================================================================
# # Original helper functions
# # ==================================================================


# def get_total_emiratewise(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return frappe.db.sql(
# 			f"""
# 			select
# 				s.vat_emirate as emirate, sum(i.base_net_amount) as total, sum(i.tax_amount)
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and i.is_exempt != 1 and i.is_zero_rated != 1
# 				{conditions}
# 			group by
# 				s.vat_emirate;
# 			""",
# 			filters,
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_emirates():
# 	return ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]


# def get_filters(filters):
# 	query_filters = []
# 	if filters.get("company"):
# 		query_filters.append(["company", "=", filters["company"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", ">=", filters["from_date"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", "<=", filters["to_date"]])
# 	return query_filters


# def get_reverse_charge_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select sum(debit)  from
# 			`tabPurchase Invoice` p inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no =  p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_reverse_charge_recoverable_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["recoverable_reverse_charge", ">", "0"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_recoverable_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select
# 			sum(debit * p.recoverable_reverse_charge / 100)
# 		from
# 			`tabPurchase Invoice` p  inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no = p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and p.recoverable_reverse_charge > 0
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_conditions_join(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and p.company=%(company)s"),
# 		("from_date", " and p.posting_date>=%(from_date)s"),
# 		("to_date", " and p.posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# def get_standard_rated_expenses_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_standard_rated_expenses_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice",
# 				filters=query_filters,
# 				fields=["sum(recoverable_standard_rated_expenses)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice",
# 				filters=query_filters,
# 				fields=["sum(tourist_tax_return)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_zero_rated_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_zero_rated = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_exempt_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_exempt = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_conditions(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and company=%(company)s"),
# 		("from_date", " and posting_date>=%(from_date)s"),
# 		("to_date", " and posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# # ==================================================================
# # "See Transactions" review screen + automatic VAT Journal Entry
# # ==================================================================

# # Accounts used for the VAT Journal Entry (names taken from your Chart of Accounts).
# # "VAT Receivable" does not exist yet: create it under Current Assets with exactly
# # this name, or change the name here to match the account you create.
# VAT_ACCOUNTS = {
# 	"output_vat": "213000 - Output VAT - OIFM",
# 	"output_vat_rcm": "213500 - Output VAT RCM - OIFM",
# 	"input_vat": "118000 - Input VAT - OIFM",
# 	"input_vat_rcm": "185000 - Input VAT RCM - OIFM",
# 	"vat_payable": "218010 - VAT Payable - OIFM",
# 	"vat_receivable": "118500 - VAT Receivable - OIFM",
# }

# # First line of the Journal Entry remark. Used to find which vouchers were already filed.
# VAT_JE_MARKER = "UAE VAT 201 |"
# VAT_SETTLE_MARKER = "UAE VAT 201 Settlement |"


# def _all_vat_rows(company, from_date, to_date):
# 	periods = (
# 		("current", from_date, to_date),
# 		("previous", add_months(from_date, -3), add_days(from_date, -1)),
# 	)
# 	rows = []
# 	for section, start, end in periods:
# 		for r in _collect_vat_transactions(company, start, end):
# 			r["section"] = section
# 			r["key"] = "{0}|{1}".format(r["category"], r["doc_name"])
# 			rows.append(r)
# 	return rows


# def get_vat_transactions(filters):
# 	"""Transactions for the VAT 201 screen.
# 	Section 'current'  : ALL transactions in the selected period (flagged ones are locked).
# 	Section 'previous' : transactions of the 3 months before the period that are NOT yet
# 	                     flagged custom_vat_filed (Sales and Purchase)."""
# 	company = filters.get("company")
# 	_check_filed_field()
# 	all_rows = _all_vat_rows(company, getdate(filters.get("from_date")), getdate(filters.get("to_date")))
# 	filed = _filed_vouchers(all_rows)

# 	rows = []
# 	for r in all_rows:
# 		r["locked"] = (r["doc_type"], r["doc_name"]) in filed
# 		if r["section"] == "previous":
# 			if r["locked"]:
# 				continue  # already filed in an earlier return -> do not show again
# 			r["note"] = _("Not previously reported")
# 		else:
# 			r["note"] = _("Already filed in a previous VAT return") if r["locked"] else ""
# 		rows.append(r)

# 	columns = [
# 		{"fieldname": "section", "label": _("Section"), "fieldtype": "Data", "width": 90},
# 		{"fieldname": "doc_name", "label": _("Document No"), "fieldtype": "Data", "width": 160},
# 		{"fieldname": "vat", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 140},
# 	]
# 	return columns, rows


# def _sales_report_rows(company, start, end, kind):
# 	"""Sales invoices exactly as the original report counts them (one row per invoice)."""
# 	if kind == "standard":
# 		item_cond = "i.is_exempt != 1 AND i.is_zero_rated != 1 AND s.vat_emirate IN %(emirates)s"
# 	elif kind == "zero":
# 		item_cond = "i.is_zero_rated = 1"
# 	else:
# 		item_cond = "i.is_exempt = 1"

# 	company_cond = " AND s.company = %(company)s" if company else ""
# 	return frappe.db.sql(
# 		f"""
# 		SELECT s.name AS doc_name, s.posting_date, s.customer_name AS party,
# 		       SUM(i.base_net_amount) AS amount, SUM(i.tax_amount) AS vat
# 		FROM `tabSales Invoice Item` i
# 		INNER JOIN `tabSales Invoice` s ON i.parent = s.name
# 		WHERE s.docstatus = 1 AND {item_cond}
# 		  AND s.posting_date >= %(start)s AND s.posting_date <= %(end)s
# 		  {company_cond}
# 		GROUP BY s.name
# 		ORDER BY s.posting_date
# 		""",
# 		{"company": company, "start": start, "end": end, "emirates": tuple(get_emirates())},
# 		as_dict=True,
# 	)


# def _collect_vat_transactions(company, start, end):
# 	out = []

# 	def add(doc_type, doc_name, posting_date, party, vtype, category, bucket, amount, vat):
# 		out.append(
# 			{
# 				"doc_type": doc_type,
# 				"doc_name": doc_name,
# 				"posting_date": str(posting_date),
# 				"party": party or "",
# 				"type": vtype,  # Sales = output VAT, Purchase = input VAT
# 				"category": category,
# 				"bucket": bucket,  # which VAT account this belongs to
# 				"amount": flt(amount),
# 				"vat": flt(vat),
# 			}
# 		)

# 	# Sales invoices - same rules as the original report's rows 1a-1g, 4 and 5:
# 	#  * Standard rated: items not zero-rated/exempt, and the invoice has a VAT Emirate set
# 	#    (VAT = sum of the item tax_amount, exactly like the summary)
# 	#  * Zero rated / Exempt: items flagged zero-rated / exempt (no VAT)
# 	for category, kind in (
# 		(_("Standard rated"), "standard"),
# 		(_("Zero rated"), "zero"),
# 		(_("Exempt"), "exempt"),
# 	):
# 		for d in _sales_report_rows(company, start, end, kind):
# 			add("Sales Invoice", d.doc_name, d.posting_date, d.party,
# 				"Sales", category, "output_vat", d.amount, d.vat if kind == "standard" else 0)

# 	# Tourist refunds (negative output VAT)
# 	tourist_filters = [
# 		["docstatus", "=", 1],
# 		["posting_date", "between", [start, end]],
# 		["tourist_tax_return", ">", 0],
# 	]
# 	if company:
# 		tourist_filters.append(["company", "=", company])
# 	for d in frappe.get_all(
# 		"Sales Invoice",
# 		filters=tourist_filters,
# 		fields=["name", "posting_date", "customer_name", "base_total", "tourist_tax_return"],
# 	):
# 		add("Sales Invoice", d.name, d.posting_date, d.customer_name, "Sales",
# 			_("Tourist refund"), "output_vat", -flt(d.base_total), -flt(d.tourist_tax_return))

# 	# Reverse charge - output side
# 	for d in _rc_sales_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Sales",
# 			_("Reverse charge (output)"), "output_vat_rcm", d.amount, d.vat_amount)

# 	# Purchases - input side
# 	for d in _std_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Standard rated expense"), "input_vat", d.amount, d.vat_amount)

# 	for d in _rc_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Reverse charge (input)"), "input_vat_rcm", d.amount, d.vat_amount)

# 	return sorted(out, key=lambda r: (r["posting_date"], r["doc_name"]))


# VAT_FILED_FIELD = "custom_vat_filed"  # Check field on Sales Invoice and Purchase Invoice
# MARK_FILED_ON_JE = True  # tick custom_vat_filed on the selected vouchers when the Journal Entry is created


# def _check_filed_field():
# 	missing = [
# 		dt for dt in ("Sales Invoice", "Purchase Invoice") if not frappe.get_meta(dt).has_field(VAT_FILED_FIELD)
# 	]
# 	if missing:
# 		frappe.throw(
# 			_("Please add a Check field named {0} to: {1}").format(VAT_FILED_FIELD, ", ".join(missing))
# 		)


# def _filed_vouchers(rows):
# 	"""Set of (doctype, name) that already have custom_vat_filed ticked."""
# 	filed = set()
# 	for dt in ("Sales Invoice", "Purchase Invoice"):
# 		names = list({r["doc_name"] for r in rows if r["doc_type"] == dt})
# 		if names:
# 			for n in frappe.get_all(dt, filters={"name": ["in", names], VAT_FILED_FIELD: 1}, pluck="name"):
# 				filed.add((dt, n))
# 	return filed


# def _build_vat_lines(totals):
# 	"""Journal Entry lines that close the VAT accounts and move the net amount to
# 	VAT Payable (output > input) or VAT Receivable (input > output)."""
# 	lines = []
# 	debit = credit = 0.0

# 	for key in ("output_vat", "output_vat_rcm"):  # output VAT has a credit balance -> debit to clear
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			lines.append({"account": VAT_ACCOUNTS[key], "debit_in_account_currency": amt})
# 			debit += amt
# 		elif amt < 0:
# 			lines.append({"account": VAT_ACCOUNTS[key], "credit_in_account_currency": -amt})
# 			credit += -amt

# 	for key in ("input_vat", "input_vat_rcm"):  # input VAT has a debit balance -> credit to clear
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			lines.append({"account": VAT_ACCOUNTS[key], "credit_in_account_currency": amt})
# 			credit += amt
# 		elif amt < 0:
# 			lines.append({"account": VAT_ACCOUNTS[key], "debit_in_account_currency": -amt})
# 			debit += -amt

# 	net = flt(debit - credit, 2)
# 	if net > 0:
# 		lines.append({"account": VAT_ACCOUNTS["vat_payable"], "credit_in_account_currency": net})
# 	elif net < 0:
# 		lines.append({"account": VAT_ACCOUNTS["vat_receivable"], "debit_in_account_currency": -net})
# 	return lines, net


# def _check_accounts(accounts):
# 	missing = [a for a in accounts if not frappe.db.exists("Account", a)]
# 	if missing:
# 		frappe.throw(
# 			_("These accounts were not found: {0}. Create them (VAT Receivable goes under Current Assets) "
# 			"or correct the names in VAT_ACCOUNTS in the report's Python file.").format(
# 				", ".join(missing)
# 			)
# 		)


# @frappe.whitelist()
# def create_vat_journal_entry(company, from_date, to_date, keys):
# 	"""Creates ONE draft Journal Entry for the selected transactions."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	keys = json.loads(keys) if isinstance(keys, str) else keys
# 	if not keys:
# 		frappe.throw(_("Please select at least one transaction."))

# 	from_date, to_date = getdate(from_date), getdate(to_date)
# 	rows = {r["key"]: r for r in _all_vat_rows(company, from_date, to_date)}

# 	selected = []
# 	for k in keys:
# 		if k not in rows:
# 			frappe.throw(_("{0} is no longer available for this return. Please reload and select again.").format(k))
# 		selected.append(rows[k])

# 	_check_filed_field()
# 	filed = _filed_vouchers(selected)
# 	already = sorted({r["doc_name"] for r in selected if (r["doc_type"], r["doc_name"]) in filed})
# 	if already:
# 		frappe.throw(_("Already included in another return: {0}").format(", ".join(already)))

# 	totals = {}
# 	for r in selected:
# 		totals[r["bucket"]] = totals.get(r["bucket"], 0) + r["vat"]

# 	lines, net = _build_vat_lines(totals)
# 	if not lines:
# 		frappe.throw(_("The selected transactions have no VAT amount to post."))
# 	_check_accounts([l["account"] for l in lines])

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Journal Entry"
# 	je.company = company
# 	je.posting_date = to_date
# 	je.user_remark = "{0} {1} | {2} to {3}\nVouchers: {4}".format(
# 		VAT_JE_MARKER,
# 		company,
# 		from_date,
# 		to_date,
# 		", ".join(sorted({r["doc_name"] for r in selected})),
# 	)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()  # stays in Draft so the accountant can review and submit

# 	if MARK_FILED_ON_JE:
# 		for dt, name in {(r["doc_type"], r["doc_name"]) for r in selected}:
# 			frappe.db.set_value(dt, name, VAT_FILED_FIELD, 1, update_modified=False)

# 	output = sum(flt(totals.get(k, 0)) for k in ("output_vat", "output_vat_rcm"))
# 	inp = sum(flt(totals.get(k, 0)) for k in ("input_vat", "input_vat_rcm"))
# 	return {
# 		"name": je.name,
# 		"output": flt(output, 2),
# 		"input": flt(inp, 2),
# 		"net": net,  # > 0 payable, < 0 receivable
# 	}


# @frappe.whitelist()
# def create_vat_settlement_entry(journal_entry, bank_account, posting_date, reference_no, reference_date):
# 	"""Payment of VAT Payable (Dr Payable, Cr Bank) or receipt of a VAT refund
# 	(Dr Bank, Cr Receivable) as a draft Bank Entry."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	src = frappe.get_doc("Journal Entry", journal_entry)
# 	if not (src.user_remark or "").startswith(VAT_JE_MARKER) or src.docstatus == 2:
# 		frappe.throw(_("{0} is not a valid VAT Journal Entry.").format(journal_entry))

# 	marker = "{0} {1}".format(VAT_SETTLE_MARKER, src.name)
# 	if frappe.db.exists(
# 		"Journal Entry", {"docstatus": ["<", 2], "user_remark": ["like", marker + "%"]}
# 	):
# 		frappe.throw(_("A payment/refund entry already exists for {0}.").format(src.name))

# 	if frappe.db.get_value("Account", bank_account, "company") != src.company:
# 		frappe.throw(_("{0} does not belong to {1}.").format(bank_account, src.company))

# 	payable = sum(
# 		flt(r.credit_in_account_currency) - flt(r.debit_in_account_currency)
# 		for r in src.accounts
# 		if r.account == VAT_ACCOUNTS["vat_payable"]
# 	)
# 	receivable = sum(
# 		flt(r.debit_in_account_currency) - flt(r.credit_in_account_currency)
# 		for r in src.accounts
# 		if r.account == VAT_ACCOUNTS["vat_receivable"]
# 	)

# 	if payable > 0:
# 		amount = flt(payable, 2)
# 		lines = [
# 			{"account": VAT_ACCOUNTS["vat_payable"], "debit_in_account_currency": amount},
# 			{"account": bank_account, "credit_in_account_currency": amount},
# 		]
# 	elif receivable > 0:
# 		amount = flt(receivable, 2)
# 		lines = [
# 			{"account": bank_account, "debit_in_account_currency": amount},
# 			{"account": VAT_ACCOUNTS["vat_receivable"], "credit_in_account_currency": amount},
# 		]
# 	else:
# 		frappe.throw(_("There is no VAT payable or receivable to settle in {0}.").format(src.name))

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Bank Entry"
# 	je.company = src.company
# 	je.posting_date = getdate(posting_date)
# 	je.cheque_no = reference_no
# 	je.cheque_date = getdate(reference_date)
# 	je.user_remark = "{0}\nVAT payment/refund for {1}".format(marker, src.name)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()
# 	return je.name





# import json
# import re

# import frappe
# from frappe import _
# from frappe.utils import add_days, add_months, flt, getdate


# def execute(filters=None):
# 	filters = filters or {}
# 	if not filters.get("company"):  # first page load runs the report with empty filters
# 		return get_columns(), []
# 	if filters.get("drilldown_key") == "vat_transactions":
# 		return get_vat_transactions(filters)
# 	if filters.get("drilldown_key"):
# 		return get_drilldown(filters)
# 	columns = get_columns()
# 	data, emirates, amounts_by_emirate = get_data(filters)
# 	return columns, data


# # ------------------------------------------------------------------
# # Summary columns
# # ------------------------------------------------------------------


# def get_columns():
# 	return [
# 		{"fieldname": "no", "label": _("No"), "fieldtype": "Data", "width": 50},
# 		{"fieldname": "legend", "label": _("Legend"), "fieldtype": "Data", "width": 300},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 125},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# # ------------------------------------------------------------------
# # Summary data
# # ------------------------------------------------------------------


# def get_data(filters=None):
# 	data = []
# 	emirates, amounts_by_emirate = append_vat_on_sales(data, filters)
# 	append_vat_on_expenses(data, filters)
# 	return data, emirates, amounts_by_emirate


# def append_vat_on_sales(data, filters):
# 	append_data(data, "", _("VAT on Sales and All Other Outputs"), "", "")

# 	emirates, amounts_by_emirate = standard_rated_expenses_emiratewise(data, filters)

# 	total_amounts = [amounts_by_emirate.get(e, {}).get("raw_amount", 0) for e in emirates]
# 	total_vat_amounts = [amounts_by_emirate.get(e, {}).get("raw_vat_amount", 0) for e in emirates]

# 	tourist_total = get_tourist_tax_return_total(filters)
# 	tourist_tax = get_tourist_tax_return_tax(filters)
# 	append_data(
# 		data,
# 		"2",
# 		_("Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme"),
# 		frappe.format((-1) * tourist_total, "Currency"),
# 		frappe.format((-1) * tourist_tax, "Currency"),
# 		drilldown_key="tourist_refund",
# 		raw_amount=(-1) * tourist_total,
# 		raw_vat_amount=(-1) * tourist_tax,
# 	)
# 	total_amounts.append((-1) * tourist_total)
# 	total_vat_amounts.append((-1) * tourist_tax)

# 	rc_total = get_reverse_charge_total(filters)
# 	rc_tax = get_reverse_charge_tax(filters)
# 	append_data(
# 		data,
# 		"3",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_total, "Currency"),
# 		frappe.format(rc_tax, "Currency"),
# 		drilldown_key="reverse_charge_sales",
# 		raw_amount=rc_total,
# 		raw_vat_amount=rc_tax,
# 	)
# 	total_amounts.append(rc_total)
# 	total_vat_amounts.append(rc_tax)

# 	zero_total = get_zero_rated_total(filters)
# 	append_data(
# 		data,
# 		"4",
# 		_("Zero Rated"),
# 		frappe.format(zero_total, "Currency"),
# 		"-",
# 		drilldown_key="zero_rated",
# 		raw_amount=zero_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(zero_total)

# 	exempt_total = get_exempt_total(filters)
# 	append_data(
# 		data,
# 		"5",
# 		_("Exempt Supplies"),
# 		frappe.format(exempt_total, "Currency"),
# 		"-",
# 		drilldown_key="exempt",
# 		raw_amount=exempt_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(exempt_total)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Sales and All Other Outputs"),
# 		frappe.format(sum(total_amounts), "Currency"),
# 		frappe.format(sum(total_vat_amounts), "Currency"),
# 	)

# 	append_data(data, "", "", "", "")

# 	return emirates, amounts_by_emirate


# def standard_rated_expenses_emiratewise(data, filters):
# 	total_emiratewise = get_total_emiratewise(filters)
# 	emirates = get_emirates()
# 	amounts_by_emirate = {}
# 	for emirate, amount, vat in total_emiratewise:
# 		amounts_by_emirate[emirate] = {
# 			"legend": emirate,
# 			"raw_amount": flt(amount),
# 			"raw_vat_amount": flt(vat),
# 			"amount": frappe.format(amount, "Currency"),
# 			"vat_amount": frappe.format(vat, "Currency"),
# 		}
# 	amounts_by_emirate = append_emiratewise_expenses(data, emirates, amounts_by_emirate)
# 	return emirates, amounts_by_emirate


# def append_emiratewise_expenses(data, emirates, amounts_by_emirate):
# 	for no, emirate in enumerate(emirates, 97):
# 		key = "standard_rated_{0}".format(emirate)
# 		if emirate in amounts_by_emirate:
# 			amounts_by_emirate[emirate]["no"] = _("1{0}").format(chr(no))
# 			amounts_by_emirate[emirate]["legend"] = _("Standard rated supplies in {0}").format(emirate)
# 			amounts_by_emirate[emirate]["drilldown_key"] = key
# 			data.append(amounts_by_emirate[emirate])
# 		else:
# 			append_data(
# 				data,
# 				_("1{0}").format(chr(no)),
# 				_("Standard rated supplies in {0}").format(emirate),
# 				frappe.format(0, "Currency"),
# 				frappe.format(0, "Currency"),
# 				drilldown_key=key,
# 				raw_amount=0,
# 				raw_vat_amount=0,
# 			)
# 	return amounts_by_emirate


# def append_vat_on_expenses(data, filters):
# 	append_data(data, "", _("VAT on Expenses and All Other Inputs"), "", "")

# 	std_exp_total = get_standard_rated_expenses_total(filters)
# 	std_exp_tax = get_standard_rated_expenses_tax(filters)
# 	append_data(
# 		data,
# 		"9",
# 		_("Standard Rated Expenses"),
# 		frappe.format(std_exp_total, "Currency"),
# 		frappe.format(std_exp_tax, "Currency"),
# 		drilldown_key="standard_rated_expenses",
# 		raw_amount=std_exp_total,
# 		raw_vat_amount=std_exp_tax,
# 	)

# 	rc_rec_total = get_reverse_charge_recoverable_total(filters)
# 	rc_rec_tax = get_reverse_charge_recoverable_tax(filters)
# 	append_data(
# 		data,
# 		"10",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_rec_total, "Currency"),
# 		frappe.format(rc_rec_tax, "Currency"),
# 		drilldown_key="reverse_charge_expenses",
# 		raw_amount=rc_rec_total,
# 		raw_vat_amount=rc_rec_tax,
# 	)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Expenses and All Other Inputs"),
# 		frappe.format(std_exp_total + rc_rec_total, "Currency"),
# 		frappe.format(std_exp_tax + rc_rec_tax, "Currency"),
# 	)


# def append_data(data, no, legend, amount, vat_amount, drilldown_key=None, raw_amount=0, raw_vat_amount=0):
# 	row = {"no": no, "legend": legend, "amount": amount, "vat_amount": vat_amount}
# 	if drilldown_key:
# 		row["drilldown_key"] = drilldown_key
# 		row["raw_amount"] = raw_amount
# 		row["raw_vat_amount"] = raw_vat_amount
# 	data.append(row)


# # ==================================================================
# # Drill-down
# # ==================================================================


# def get_drilldown(filters):
# 	key = filters.get("drilldown_key")
# 	company = filters.get("company")
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")

# 	purchase_keys = ("standard_rated_expenses", "reverse_charge_expenses", "expenses_total")
# 	if key in purchase_keys:
# 		columns, data = _get_purchase_detail(key, company, from_date, to_date)
# 	elif key == "reverse_charge_sales":
# 		columns = _purchase_detail_columns()
# 		data = _rc_sales_detail(company, from_date, to_date)
# 	else:
# 		columns, data = _get_sales_detail(key, company, from_date, to_date)

# 	return columns, data, None, None, None, True


# def _get_sales_detail(key, company, from_date, to_date):
# 	if key.startswith("standard_rated_"):
# 		emirate = key[len("standard_rated_") :]
# 		return _sales_invoice_breakdown(company, from_date, to_date, emirate=emirate)
# 	elif key == "tourist_refund":
# 		return _sales_invoice_breakdown(company, from_date, to_date, tourist_only=True)
# 	elif key == "zero_rated":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_zero_rated=True)
# 	elif key == "exempt":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_exempt=True)
# 	elif key == "sales_total":
# 		return _sales_invoice_breakdown(company, from_date, to_date)
# 	return [], []


# def _get_purchase_detail(key, company, from_date, to_date):
# 	columns = _purchase_detail_columns()
# 	if key == "standard_rated_expenses":
# 		data = _std_expenses_detail(company, from_date, to_date)
# 	elif key == "reverse_charge_expenses":
# 		data = _rc_expenses_detail(company, from_date, to_date)
# 	elif key == "expenses_total":
# 		data = _all_expenses_detail(company, from_date, to_date)
# 	else:
# 		data = []
# 	return columns, data


# def _purchase_detail_columns():
# 	return [
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{
# 			"fieldname": "doc_name",
# 			"label": _("Document No"),
# 			"fieldtype": "Dynamic Link",
# 			"options": "doc_type",
# 			"width": 180,
# 		},
# 		{"fieldname": "party", "label": _("Party"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "item", "label": _("Item"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 130},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# def _account_fieldname(account):
# 	"""Sanitize an account name for use as a column fieldname."""
# 	return "acc_" + re.sub(r"[^a-zA-Z0-9_]", "_", account)


# def _sales_invoice_breakdown(
# 	company, from_date, to_date, emirate=None, is_zero_rated=False, is_exempt=False, tourist_only=False
# ):
# 	"""Account-wise breakdown of qualifying Sales Invoices."""
# 	si_cond, si_params = _si_conditions(company, from_date, to_date)

# 	if tourist_only:
# 		invoices = frappe.db.sql_list(
# 			"SELECT si.name FROM `tabSales Invoice` si WHERE 1=1 "
# 			+ si_cond + " AND si.tourist_tax_return > 0",
# 			tuple(si_params),
# 		)
# 	else:
# 		item_cond = ""
# 		item_params = []
# 		if emirate:
# 			item_cond += " AND si.vat_emirate = %s"
# 			item_params.append(emirate)
# 		if is_zero_rated:
# 			item_cond += " AND sii.is_zero_rated = 1"
# 		elif is_exempt:
# 			item_cond += " AND sii.is_exempt = 1"
# 		else:
# 			item_cond += " AND sii.is_exempt != 1 AND sii.is_zero_rated != 1"

# 		invoices = frappe.db.sql_list(
# 			"SELECT DISTINCT si.name FROM `tabSales Invoice Item` sii "
# 			"INNER JOIN `tabSales Invoice` si ON si.name = sii.parent "
# 			"WHERE 1=1 " + si_cond + item_cond,
# 			tuple(si_params + item_params),
# 		)

# 	if not invoices:
# 		return _sales_breakdown_columns([], []), []

# 	invoices_tuple = tuple(invoices)

# 	headers = frappe.db.sql(
# 		"""
# 		SELECT si.name AS sales_invoice, si.posting_date, si.customer_name AS customer,
# 		       si.debit_to AS receivable_account, si.vat_emirate
# 		FROM `tabSales Invoice` si
# 		WHERE si.docstatus = 1 AND si.name IN %s
# 		ORDER BY si.posting_date
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	items = frappe.db.sql(
# 		"""
# 		SELECT sii.parent AS sales_invoice, sii.income_account, sii.base_net_amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# 		WHERE si.docstatus = 1 AND sii.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	taxes = frappe.db.sql(
# 		"""
# 		SELECT stc.parent AS sales_invoice, stc.account_head, stc.base_tax_amount
# 		FROM `tabSales Taxes and Charges` stc
# 		INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
# 		WHERE si.docstatus = 1 AND stc.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	income_accounts = sorted({r.income_account for r in items if r.income_account})
# 	tax_accounts = sorted({r.account_head for r in taxes if r.account_head})

# 	item_map = {}
# 	for r in items:
# 		item_map.setdefault(r.sales_invoice, []).append(r)

# 	tax_map = {}
# 	for r in taxes:
# 		tax_map.setdefault(r.sales_invoice, []).append(r)

# 	data = []
# 	for h in headers:
# 		row = {
# 			"voucher_type": "Sales Invoice",
# 			"sales_invoice": h.sales_invoice,
# 			"posting_date": h.posting_date,
# 			"customer": h.customer,
# 			"receivable_account": h.receivable_account,
# 			"vat_emirate": h.vat_emirate,
# 		}
# 		for acc in income_accounts:
# 			row[_account_fieldname(acc)] = 0
# 		for acc in tax_accounts:
# 			row[_account_fieldname(acc)] = 0

# 		net_total = 0
# 		for it in item_map.get(h.sales_invoice, []):
# 			net_total += flt(it.base_net_amount)
# 			if it.income_account:
# 				row[_account_fieldname(it.income_account)] = flt(row[_account_fieldname(it.income_account)]) + flt(
# 					it.base_net_amount
# 				)

# 		tax_total = 0
# 		for t in tax_map.get(h.sales_invoice, []):
# 			tax_total += flt(t.base_tax_amount)
# 			if t.account_head:
# 				row[_account_fieldname(t.account_head)] = flt(row[_account_fieldname(t.account_head)]) + flt(
# 					t.base_tax_amount
# 				)

# 		row["net_total"] = flt(net_total)
# 		row["tax_total"] = flt(tax_total)
# 		row["grand_total"] = flt(net_total + tax_total)
# 		data.append(row)

# 	columns = _sales_breakdown_columns(income_accounts, tax_accounts)
# 	return columns, data


# def _sales_breakdown_columns(income_accounts, tax_accounts):
# 	columns = [
# 		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 110},
# 		{
# 			"fieldname": "sales_invoice",
# 			"label": _("Sales Invoice No"),
# 			"fieldtype": "Link",
# 			"options": "Sales Invoice",
# 			"width": 150,
# 		},
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{"fieldname": "vat_emirate", "label": _("VAT Emirates"), "fieldtype": "Data", "width": 140},
# 		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 220},
# 		{"fieldname": "receivable_account", "label": _("Receivable Account"), "fieldtype": "Data", "width": 220},
# 	]
# 	for acc in income_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	for acc in tax_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	columns.extend(
# 		[
# 			{"fieldname": "net_total", "label": _("Net Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "tax_total", "label": _("Tax Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 150},
# 		]
# 	)
# 	return columns


# # ------------------------------------------------------------------
# # Condition builders
# # ------------------------------------------------------------------


# def _si_conditions(company, from_date, to_date):
# 	cond = "AND si.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND si.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND si.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND si.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _pi_conditions(company, from_date, to_date):
# 	cond = "AND pi.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND pi.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND pi.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND pi.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _gl_conditions(company):
# 	cond = "AND gl.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND gl.account IN (SELECT account FROM `tabUAE VAT Account` WHERE parent = %s)"
# 		params.append(company)
# 	return cond, params


# # ------------------------------------------------------------------
# # Sales-side detail queries
# # ------------------------------------------------------------------


# def _rc_sales_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, SUM(gl.debit) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Purchase-side detail queries
# # ------------------------------------------------------------------


# def _std_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	cond += " AND pi.recoverable_standard_rated_expenses > 0"

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		WHERE 1=1 {cond}
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# def _rc_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' AND pi.recoverable_reverse_charge > 0 " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount,
# 		       SUM(gl.debit * pi.recoverable_reverse_charge / 100) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Combined detail queries
# # ------------------------------------------------------------------


# def _all_expenses_detail(company, from_date, to_date):
# 	data = []
# 	data.extend(_std_expenses_detail(company, from_date, to_date))
# 	data.extend(_rc_expenses_detail(company, from_date, to_date))
# 	return data


# # ==================================================================
# # Original helper functions
# # ==================================================================


# def get_total_emiratewise(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return frappe.db.sql(
# 			f"""
# 			select
# 				s.vat_emirate as emirate, sum(i.base_net_amount) as total, sum(i.tax_amount)
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and i.is_exempt != 1 and i.is_zero_rated != 1
# 				{conditions}
# 			group by
# 				s.vat_emirate;
# 			""",
# 			filters,
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_emirates():
# 	return ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]


# def get_filters(filters):
# 	query_filters = []
# 	if filters.get("company"):
# 		query_filters.append(["company", "=", filters["company"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", ">=", filters["from_date"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", "<=", filters["to_date"]])
# 	return query_filters


# def get_reverse_charge_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select sum(debit)  from
# 			`tabPurchase Invoice` p inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no =  p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_reverse_charge_recoverable_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["recoverable_reverse_charge", ">", "0"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_recoverable_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select
# 			sum(debit * p.recoverable_reverse_charge / 100)
# 		from
# 			`tabPurchase Invoice` p  inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no = p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and p.recoverable_reverse_charge > 0
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_conditions_join(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and p.company=%(company)s"),
# 		("from_date", " and p.posting_date>=%(from_date)s"),
# 		("to_date", " and p.posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# def get_standard_rated_expenses_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_standard_rated_expenses_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice",
# 				filters=query_filters,
# 				fields=["sum(recoverable_standard_rated_expenses)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice",
# 				filters=query_filters,
# 				fields=["sum(tourist_tax_return)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_zero_rated_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_zero_rated = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_exempt_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_exempt = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_conditions(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and company=%(company)s"),
# 		("from_date", " and posting_date>=%(from_date)s"),
# 		("to_date", " and posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# # ==================================================================
# # "See Transactions" review screen + automatic VAT Journal Entry
# # ==================================================================

# # VAT accounts used for the VAT Journal Entry.
# # Every company has its own chart of accounts, so we only store the ACCOUNT NUMBER here
# # (same number in all companies). The real account is looked up for the company selected
# # in the report, e.g. 213000 -> "213000 - Output VAT - OBR" for Orion Bus Rental.
# VAT_ACCOUNT_NUMBERS = {
# 	"output_vat": "213000",
# 	"output_vat_rcm": "213500",
# 	"input_vat": "118000",
# 	"input_vat_rcm": "185000",
# 	"vat_payable": "218010",
# 	"vat_receivable": "118500",
# }

# VAT_ACCOUNT_LABELS = {
# 	"output_vat": "Output VAT",
# 	"output_vat_rcm": "Output VAT RCM",
# 	"input_vat": "Input VAT",
# 	"input_vat_rcm": "Input VAT RCM",
# 	"vat_payable": "VAT Payable",
# 	"vat_receivable": "VAT Receivable",
# }


# def _vat_accounts(company):
# 	"""Returns {"output_vat": "<full account name of THIS company>", ...}."""
# 	accounts, missing = {}, []
# 	abbr = frappe.get_cached_value("Company", company, "abbr")
# 	for key, number in VAT_ACCOUNT_NUMBERS.items():
# 		name = frappe.db.get_value(
# 			"Account", {"company": company, "account_number": number, "is_group": 0}, "name"
# 		)
# 		if not name:  # fallback: "<number> - <label> - <abbr>"
# 			guess = "{0} - {1} - {2}".format(number, VAT_ACCOUNT_LABELS[key], abbr)
# 			if frappe.db.exists("Account", {"name": guess, "company": company, "is_group": 0}):
# 				name = guess
# 		if name:
# 			accounts[key] = name
# 		else:
# 			missing.append("{0} ({1})".format(number, VAT_ACCOUNT_LABELS[key]))
# 	if missing:
# 		frappe.throw(
# 			_("{0} does not have these VAT accounts: {1}. Create them (account number must match) and try again.").format(
# 				company, ", ".join(missing)
# 			)
# 		)
# 	return accounts


# # First line of the Journal Entry remark. Used to find which vouchers were already filed.
# VAT_JE_MARKER = "UAE VAT 201 |"
# VAT_SETTLE_MARKER = "UAE VAT 201 Settlement |"


# def _all_vat_rows(company, from_date, to_date):
# 	periods = (
# 		("current", from_date, to_date),
# 		("previous", add_months(from_date, -3), add_days(from_date, -1)),
# 	)
# 	rows = []
# 	for section, start, end in periods:
# 		for r in _collect_vat_transactions(company, start, end):
# 			r["section"] = section
# 			r["key"] = "{0}|{1}".format(r["category"], r["doc_name"])
# 			rows.append(r)
# 	return rows


# def get_vat_transactions(filters):
# 	"""Transactions for the VAT 201 screen.
# 	Section 'current'  : ALL transactions in the selected period (flagged ones are locked).
# 	Section 'previous' : transactions of the 3 months before the period that are NOT yet
# 	                     flagged custom_vat_filed (Sales and Purchase)."""
# 	company = filters.get("company")
# 	_check_filed_field()
# 	all_rows = _all_vat_rows(company, getdate(filters.get("from_date")), getdate(filters.get("to_date")))
# 	filed = _filed_vouchers(all_rows)

# 	rows = []
# 	for r in all_rows:
# 		r["locked"] = (r["doc_type"], r["doc_name"]) in filed
# 		if r["section"] == "previous":
# 			if r["locked"]:
# 				continue  # already filed in an earlier return -> do not show again
# 			r["note"] = _("Not previously reported")
# 		else:
# 			r["note"] = _("Already filed in a previous VAT return") if r["locked"] else ""
# 		rows.append(r)

# 	columns = [
# 		{"fieldname": "section", "label": _("Section"), "fieldtype": "Data", "width": 90},
# 		{"fieldname": "doc_name", "label": _("Document No"), "fieldtype": "Data", "width": 160},
# 		{"fieldname": "vat", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 140},
# 	]
# 	return columns, rows


# def _sales_report_rows(company, start, end, kind):
# 	"""Sales invoices exactly as the original report counts them (one row per invoice)."""
# 	if kind == "standard":
# 		item_cond = "i.is_exempt != 1 AND i.is_zero_rated != 1 AND s.vat_emirate IN %(emirates)s"
# 	elif kind == "zero":
# 		item_cond = "i.is_zero_rated = 1"
# 	else:
# 		item_cond = "i.is_exempt = 1"

# 	company_cond = " AND s.company = %(company)s" if company else ""
# 	return frappe.db.sql(
# 		f"""
# 		SELECT s.name AS doc_name, s.posting_date, s.customer_name AS party,
# 		       SUM(i.base_net_amount) AS amount, SUM(i.tax_amount) AS vat
# 		FROM `tabSales Invoice Item` i
# 		INNER JOIN `tabSales Invoice` s ON i.parent = s.name
# 		WHERE s.docstatus = 1 AND {item_cond}
# 		  AND s.posting_date >= %(start)s AND s.posting_date <= %(end)s
# 		  {company_cond}
# 		GROUP BY s.name
# 		ORDER BY s.posting_date
# 		""",
# 		{"company": company, "start": start, "end": end, "emirates": tuple(get_emirates())},
# 		as_dict=True,
# 	)


# def _collect_vat_transactions(company, start, end):
# 	out = []

# 	def add(doc_type, doc_name, posting_date, party, vtype, category, bucket, amount, vat):
# 		out.append(
# 			{
# 				"doc_type": doc_type,
# 				"doc_name": doc_name,
# 				"posting_date": str(posting_date),
# 				"party": party or "",
# 				"type": vtype,  # Sales = output VAT, Purchase = input VAT
# 				"category": category,
# 				"bucket": bucket,  # which VAT account this belongs to
# 				"amount": flt(amount),
# 				"vat": flt(vat),
# 			}
# 		)

# 	# Sales invoices - same rules as the original report's rows 1a-1g, 4 and 5:
# 	#  * Standard rated: items not zero-rated/exempt, and the invoice has a VAT Emirate set
# 	#    (VAT = sum of the item tax_amount, exactly like the summary)
# 	#  * Zero rated / Exempt: items flagged zero-rated / exempt (no VAT)
# 	for category, kind in (
# 		(_("Standard rated"), "standard"),
# 		(_("Zero rated"), "zero"),
# 		(_("Exempt"), "exempt"),
# 	):
# 		for d in _sales_report_rows(company, start, end, kind):
# 			add("Sales Invoice", d.doc_name, d.posting_date, d.party,
# 				"Sales", category, "output_vat", d.amount, d.vat if kind == "standard" else 0)

# 	# Tourist refunds (negative output VAT)
# 	tourist_filters = [
# 		["docstatus", "=", 1],
# 		["posting_date", "between", [start, end]],
# 		["tourist_tax_return", ">", 0],
# 	]
# 	if company:
# 		tourist_filters.append(["company", "=", company])
# 	for d in frappe.get_all(
# 		"Sales Invoice",
# 		filters=tourist_filters,
# 		fields=["name", "posting_date", "customer_name", "base_total", "tourist_tax_return"],
# 	):
# 		add("Sales Invoice", d.name, d.posting_date, d.customer_name, "Sales",
# 			_("Tourist refund"), "output_vat", -flt(d.base_total), -flt(d.tourist_tax_return))

# 	# Reverse charge - output side
# 	for d in _rc_sales_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Sales",
# 			_("Reverse charge (output)"), "output_vat_rcm", d.amount, d.vat_amount)

# 	# Purchases - input side
# 	for d in _std_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Standard rated expense"), "input_vat", d.amount, d.vat_amount)

# 	for d in _rc_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Reverse charge (input)"), "input_vat_rcm", d.amount, d.vat_amount)

# 	return sorted(out, key=lambda r: (r["posting_date"], r["doc_name"]))


# VAT_FILED_FIELD = "custom_vat_filed"  # Check field on Sales Invoice and Purchase Invoice
# MARK_FILED_ON_JE = True  # tick custom_vat_filed on the selected vouchers when the Journal Entry is created


# def _check_filed_field():
# 	missing = [
# 		dt for dt in ("Sales Invoice", "Purchase Invoice") if not frappe.get_meta(dt).has_field(VAT_FILED_FIELD)
# 	]
# 	if missing:
# 		frappe.throw(
# 			_("Please add a Check field named {0} to: {1}").format(VAT_FILED_FIELD, ", ".join(missing))
# 		)


# def _filed_vouchers(rows):
# 	"""Set of (doctype, name) that already have custom_vat_filed ticked."""
# 	filed = set()
# 	for dt in ("Sales Invoice", "Purchase Invoice"):
# 		names = list({r["doc_name"] for r in rows if r["doc_type"] == dt})
# 		if names:
# 			for n in frappe.get_all(dt, filters={"name": ["in", names], VAT_FILED_FIELD: 1}, pluck="name"):
# 				filed.add((dt, n))
# 	return filed


# def _build_vat_lines(totals, accounts):
# 	"""Journal Entry lines that close the VAT accounts and move the net amount to
# 	VAT Payable (output > input) or VAT Receivable (input > output)."""
# 	lines = []
# 	debit = credit = 0.0

# 	for key in ("output_vat", "output_vat_rcm"):  # output VAT has a credit balance -> debit to clear
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			lines.append({"account": accounts[key], "debit_in_account_currency": amt})
# 			debit += amt
# 		elif amt < 0:
# 			lines.append({"account": accounts[key], "credit_in_account_currency": -amt})
# 			credit += -amt

# 	for key in ("input_vat", "input_vat_rcm"):  # input VAT has a debit balance -> credit to clear
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			lines.append({"account": accounts[key], "credit_in_account_currency": amt})
# 			credit += amt
# 		elif amt < 0:
# 			lines.append({"account": accounts[key], "debit_in_account_currency": -amt})
# 			debit += -amt

# 	net = flt(debit - credit, 2)
# 	if net > 0:
# 		lines.append({"account": accounts["vat_payable"], "credit_in_account_currency": net})
# 	elif net < 0:
# 		lines.append({"account": accounts["vat_receivable"], "debit_in_account_currency": -net})
# 	return lines, net


# def _check_accounts(accounts):
# 	missing = [a for a in accounts if not frappe.db.exists("Account", a)]
# 	if missing:
# 		frappe.throw(
# 			_("These accounts were not found: {0}. Create them (VAT Receivable goes under Current Assets) "
# 			"or correct VAT_ACCOUNT_NUMBERS in the report's Python file.").format(
# 				", ".join(missing)
# 			)
# 		)


# @frappe.whitelist()
# def create_vat_journal_entry(company, from_date, to_date, keys):
# 	"""Creates ONE draft Journal Entry for the selected transactions."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	keys = json.loads(keys) if isinstance(keys, str) else keys
# 	if not keys:
# 		frappe.throw(_("Please select at least one transaction."))

# 	from_date, to_date = getdate(from_date), getdate(to_date)
# 	rows = {r["key"]: r for r in _all_vat_rows(company, from_date, to_date)}

# 	selected = []
# 	for k in keys:
# 		if k not in rows:
# 			frappe.throw(_("{0} is no longer available for this return. Please reload and select again.").format(k))
# 		selected.append(rows[k])

# 	_check_filed_field()
# 	filed = _filed_vouchers(selected)
# 	already = sorted({r["doc_name"] for r in selected if (r["doc_type"], r["doc_name"]) in filed})
# 	if already:
# 		frappe.throw(_("Already included in another return: {0}").format(", ".join(already)))

# 	totals = {}
# 	for r in selected:
# 		totals[r["bucket"]] = totals.get(r["bucket"], 0) + r["vat"]

# 	accounts = _vat_accounts(company)
# 	lines, net = _build_vat_lines(totals, accounts)
# 	if not lines:
# 		frappe.throw(_("The selected transactions have no VAT amount to post."))
# 	_check_accounts([l["account"] for l in lines])

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Journal Entry"
# 	je.company = company
# 	je.posting_date = to_date
# 	je.user_remark = "{0} {1} | {2} to {3}\nVouchers: {4}".format(
# 		VAT_JE_MARKER,
# 		company,
# 		from_date,
# 		to_date,
# 		", ".join(sorted({r["doc_name"] for r in selected})),
# 	)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()  # stays in Draft so the accountant can review and submit

# 	if MARK_FILED_ON_JE:
# 		for dt, name in {(r["doc_type"], r["doc_name"]) for r in selected}:
# 			frappe.db.set_value(dt, name, VAT_FILED_FIELD, 1, update_modified=False)

# 	output = sum(flt(totals.get(k, 0)) for k in ("output_vat", "output_vat_rcm"))
# 	inp = sum(flt(totals.get(k, 0)) for k in ("input_vat", "input_vat_rcm"))
# 	return {
# 		"name": je.name,
# 		"output": flt(output, 2),
# 		"input": flt(inp, 2),
# 		"net": net,  # > 0 payable, < 0 receivable
# 	}


# @frappe.whitelist()
# def create_vat_settlement_entry(journal_entry, bank_account, posting_date, reference_no, reference_date):
# 	"""Payment of VAT Payable (Dr Payable, Cr Bank) or receipt of a VAT refund
# 	(Dr Bank, Cr Receivable) as a draft Bank Entry."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	src = frappe.get_doc("Journal Entry", journal_entry)
# 	if not (src.user_remark or "").startswith(VAT_JE_MARKER) or src.docstatus == 2:
# 		frappe.throw(_("{0} is not a valid VAT Journal Entry.").format(journal_entry))

# 	marker = "{0} {1}".format(VAT_SETTLE_MARKER, src.name)
# 	if frappe.db.exists(
# 		"Journal Entry", {"docstatus": ["<", 2], "user_remark": ["like", marker + "%"]}
# 	):
# 		frappe.throw(_("A payment/refund entry already exists for {0}.").format(src.name))

# 	accounts = _vat_accounts(src.company)
# 	if frappe.db.get_value("Account", bank_account, "company") != src.company:
# 		frappe.throw(_("{0} does not belong to {1}.").format(bank_account, src.company))

# 	payable = sum(
# 		flt(r.credit_in_account_currency) - flt(r.debit_in_account_currency)
# 		for r in src.accounts
# 		if r.account == accounts["vat_payable"]
# 	)
# 	receivable = sum(
# 		flt(r.debit_in_account_currency) - flt(r.credit_in_account_currency)
# 		for r in src.accounts
# 		if r.account == accounts["vat_receivable"]
# 	)

# 	if payable > 0:
# 		amount = flt(payable, 2)
# 		lines = [
# 			{"account": accounts["vat_payable"], "debit_in_account_currency": amount},
# 			{"account": bank_account, "credit_in_account_currency": amount},
# 		]
# 	elif receivable > 0:
# 		amount = flt(receivable, 2)
# 		lines = [
# 			{"account": bank_account, "debit_in_account_currency": amount},
# 			{"account": accounts["vat_receivable"], "credit_in_account_currency": amount},
# 		]
# 	else:
# 		frappe.throw(_("There is no VAT payable or receivable to settle in {0}.").format(src.name))

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Bank Entry"
# 	je.company = src.company
# 	je.posting_date = getdate(posting_date)
# 	je.cheque_no = reference_no
# 	je.cheque_date = getdate(reference_date)
# 	je.user_remark = "{0}\nVAT payment/refund for {1}".format(marker, src.name)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()
# 	return je.name


# import json
# import re

# import frappe
# from frappe import _
# from frappe.utils import add_days, add_months, flt, getdate


# def execute(filters=None):
# 	filters = filters or {}
# 	if not filters.get("company"):  # first page load runs the report with empty filters
# 		return get_columns(), []
# 	if filters.get("drilldown_key") == "vat_transactions":
# 		return get_vat_transactions(filters)
# 	if filters.get("drilldown_key"):
# 		return get_drilldown(filters)
# 	columns = get_columns()
# 	data, emirates, amounts_by_emirate = get_data(filters)
# 	return columns, data


# # ------------------------------------------------------------------
# # Summary columns
# # ------------------------------------------------------------------


# def get_columns():
# 	return [
# 		{"fieldname": "no", "label": _("No"), "fieldtype": "Data", "width": 50},
# 		{"fieldname": "legend", "label": _("Legend"), "fieldtype": "Data", "width": 300},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 125},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# # ------------------------------------------------------------------
# # Summary data
# # ------------------------------------------------------------------


# def get_data(filters=None):
# 	data = []
# 	emirates, amounts_by_emirate = append_vat_on_sales(data, filters)
# 	append_vat_on_expenses(data, filters)
# 	return data, emirates, amounts_by_emirate


# def append_vat_on_sales(data, filters):
# 	append_data(data, "", _("VAT on Sales and All Other Outputs"), "", "")

# 	emirates, amounts_by_emirate = standard_rated_expenses_emiratewise(data, filters)

# 	total_amounts = [amounts_by_emirate.get(e, {}).get("raw_amount", 0) for e in emirates]
# 	total_vat_amounts = [amounts_by_emirate.get(e, {}).get("raw_vat_amount", 0) for e in emirates]

# 	tourist_total = get_tourist_tax_return_total(filters)
# 	tourist_tax = get_tourist_tax_return_tax(filters)
# 	append_data(
# 		data,
# 		"2",
# 		_("Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme"),
# 		frappe.format((-1) * tourist_total, "Currency"),
# 		frappe.format((-1) * tourist_tax, "Currency"),
# 		drilldown_key="tourist_refund",
# 		raw_amount=(-1) * tourist_total,
# 		raw_vat_amount=(-1) * tourist_tax,
# 	)
# 	total_amounts.append((-1) * tourist_total)
# 	total_vat_amounts.append((-1) * tourist_tax)

# 	rc_total = get_reverse_charge_total(filters)
# 	rc_tax = get_reverse_charge_tax(filters)
# 	append_data(
# 		data,
# 		"3",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_total, "Currency"),
# 		frappe.format(rc_tax, "Currency"),
# 		drilldown_key="reverse_charge_sales",
# 		raw_amount=rc_total,
# 		raw_vat_amount=rc_tax,
# 	)
# 	total_amounts.append(rc_total)
# 	total_vat_amounts.append(rc_tax)

# 	zero_total = get_zero_rated_total(filters)
# 	append_data(
# 		data,
# 		"4",
# 		_("Zero Rated"),
# 		frappe.format(zero_total, "Currency"),
# 		"-",
# 		drilldown_key="zero_rated",
# 		raw_amount=zero_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(zero_total)

# 	exempt_total = get_exempt_total(filters)
# 	append_data(
# 		data,
# 		"5",
# 		_("Exempt Supplies"),
# 		frappe.format(exempt_total, "Currency"),
# 		"-",
# 		drilldown_key="exempt",
# 		raw_amount=exempt_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(exempt_total)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Sales and All Other Outputs"),
# 		frappe.format(sum(total_amounts), "Currency"),
# 		frappe.format(sum(total_vat_amounts), "Currency"),
# 	)

# 	append_data(data, "", "", "", "")

# 	return emirates, amounts_by_emirate


# def standard_rated_expenses_emiratewise(data, filters):
# 	total_emiratewise = get_total_emiratewise(filters)
# 	emirates = get_emirates()
# 	amounts_by_emirate = {}
# 	for emirate, amount, vat in total_emiratewise:
# 		amounts_by_emirate[emirate] = {
# 			"legend": emirate,
# 			"raw_amount": flt(amount),
# 			"raw_vat_amount": flt(vat),
# 			"amount": frappe.format(amount, "Currency"),
# 			"vat_amount": frappe.format(vat, "Currency"),
# 		}
# 	amounts_by_emirate = append_emiratewise_expenses(data, emirates, amounts_by_emirate)
# 	return emirates, amounts_by_emirate


# def append_emiratewise_expenses(data, emirates, amounts_by_emirate):
# 	for no, emirate in enumerate(emirates, 97):
# 		key = "standard_rated_{0}".format(emirate)
# 		if emirate in amounts_by_emirate:
# 			amounts_by_emirate[emirate]["no"] = _("1{0}").format(chr(no))
# 			amounts_by_emirate[emirate]["legend"] = _("Standard rated supplies in {0}").format(emirate)
# 			amounts_by_emirate[emirate]["drilldown_key"] = key
# 			data.append(amounts_by_emirate[emirate])
# 		else:
# 			append_data(
# 				data,
# 				_("1{0}").format(chr(no)),
# 				_("Standard rated supplies in {0}").format(emirate),
# 				frappe.format(0, "Currency"),
# 				frappe.format(0, "Currency"),
# 				drilldown_key=key,
# 				raw_amount=0,
# 				raw_vat_amount=0,
# 			)
# 	return amounts_by_emirate


# def append_vat_on_expenses(data, filters):
# 	append_data(data, "", _("VAT on Expenses and All Other Inputs"), "", "")

# 	std_exp_total = get_standard_rated_expenses_total(filters)
# 	std_exp_tax = get_standard_rated_expenses_tax(filters)
# 	append_data(
# 		data,
# 		"9",
# 		_("Standard Rated Expenses"),
# 		frappe.format(std_exp_total, "Currency"),
# 		frappe.format(std_exp_tax, "Currency"),
# 		drilldown_key="standard_rated_expenses",
# 		raw_amount=std_exp_total,
# 		raw_vat_amount=std_exp_tax,
# 	)

# 	rc_rec_total = get_reverse_charge_recoverable_total(filters)
# 	rc_rec_tax = get_reverse_charge_recoverable_tax(filters)
# 	append_data(
# 		data,
# 		"10",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_rec_total, "Currency"),
# 		frappe.format(rc_rec_tax, "Currency"),
# 		drilldown_key="reverse_charge_expenses",
# 		raw_amount=rc_rec_total,
# 		raw_vat_amount=rc_rec_tax,
# 	)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Expenses and All Other Inputs"),
# 		frappe.format(std_exp_total + rc_rec_total, "Currency"),
# 		frappe.format(std_exp_tax + rc_rec_tax, "Currency"),
# 	)


# def append_data(data, no, legend, amount, vat_amount, drilldown_key=None, raw_amount=0, raw_vat_amount=0):
# 	row = {"no": no, "legend": legend, "amount": amount, "vat_amount": vat_amount}
# 	if drilldown_key:
# 		row["drilldown_key"] = drilldown_key
# 		row["raw_amount"] = raw_amount
# 		row["raw_vat_amount"] = raw_vat_amount
# 	data.append(row)


# # ==================================================================
# # Drill-down
# # ==================================================================


# def get_drilldown(filters):
# 	key = filters.get("drilldown_key")
# 	company = filters.get("company")
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")

# 	purchase_keys = ("standard_rated_expenses", "reverse_charge_expenses", "expenses_total")
# 	if key in purchase_keys:
# 		columns, data = _get_purchase_detail(key, company, from_date, to_date)
# 	elif key == "reverse_charge_sales":
# 		columns = _purchase_detail_columns()
# 		data = _rc_sales_detail(company, from_date, to_date)
# 	else:
# 		columns, data = _get_sales_detail(key, company, from_date, to_date)

# 	return columns, data, None, None, None, True


# def _get_sales_detail(key, company, from_date, to_date):
# 	if key.startswith("standard_rated_"):
# 		emirate = key[len("standard_rated_") :]
# 		return _sales_invoice_breakdown(company, from_date, to_date, emirate=emirate)
# 	elif key == "tourist_refund":
# 		return _sales_invoice_breakdown(company, from_date, to_date, tourist_only=True)
# 	elif key == "zero_rated":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_zero_rated=True)
# 	elif key == "exempt":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_exempt=True)
# 	elif key == "sales_total":
# 		return _sales_invoice_breakdown(company, from_date, to_date)
# 	return [], []


# def _get_purchase_detail(key, company, from_date, to_date):
# 	columns = _purchase_detail_columns()
# 	if key == "standard_rated_expenses":
# 		data = _std_expenses_detail(company, from_date, to_date)
# 	elif key == "reverse_charge_expenses":
# 		data = _rc_expenses_detail(company, from_date, to_date)
# 	elif key == "expenses_total":
# 		data = _all_expenses_detail(company, from_date, to_date)
# 	else:
# 		data = []
# 	return columns, data


# def _purchase_detail_columns():
# 	return [
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{
# 			"fieldname": "doc_name",
# 			"label": _("Document No"),
# 			"fieldtype": "Dynamic Link",
# 			"options": "doc_type",
# 			"width": 180,
# 		},
# 		{"fieldname": "party", "label": _("Party"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "item", "label": _("Item"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 130},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# def _account_fieldname(account):
# 	"""Sanitize an account name for use as a column fieldname."""
# 	return "acc_" + re.sub(r"[^a-zA-Z0-9_]", "_", account)


# def _sales_invoice_breakdown(
# 	company, from_date, to_date, emirate=None, is_zero_rated=False, is_exempt=False, tourist_only=False
# ):
# 	"""Account-wise breakdown of qualifying Sales Invoices."""
# 	si_cond, si_params = _si_conditions(company, from_date, to_date)

# 	if tourist_only:
# 		invoices = frappe.db.sql_list(
# 			"SELECT si.name FROM `tabSales Invoice` si WHERE 1=1 "
# 			+ si_cond + " AND si.tourist_tax_return > 0",
# 			tuple(si_params),
# 		)
# 	else:
# 		item_cond = ""
# 		item_params = []
# 		if emirate:
# 			item_cond += " AND si.vat_emirate = %s"
# 			item_params.append(emirate)
# 		if is_zero_rated:
# 			item_cond += " AND sii.is_zero_rated = 1"
# 		elif is_exempt:
# 			item_cond += " AND sii.is_exempt = 1"
# 		else:
# 			item_cond += " AND sii.is_exempt != 1 AND sii.is_zero_rated != 1"

# 		invoices = frappe.db.sql_list(
# 			"SELECT DISTINCT si.name FROM `tabSales Invoice Item` sii "
# 			"INNER JOIN `tabSales Invoice` si ON si.name = sii.parent "
# 			"WHERE 1=1 " + si_cond + item_cond,
# 			tuple(si_params + item_params),
# 		)

# 	if not invoices:
# 		return _sales_breakdown_columns([], []), []

# 	invoices_tuple = tuple(invoices)

# 	headers = frappe.db.sql(
# 		"""
# 		SELECT si.name AS sales_invoice, si.posting_date, si.customer_name AS customer,
# 		       si.debit_to AS receivable_account, si.vat_emirate
# 		FROM `tabSales Invoice` si
# 		WHERE si.docstatus = 1 AND si.name IN %s
# 		ORDER BY si.posting_date
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	items = frappe.db.sql(
# 		"""
# 		SELECT sii.parent AS sales_invoice, sii.income_account, sii.base_net_amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# 		WHERE si.docstatus = 1 AND sii.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	taxes = frappe.db.sql(
# 		"""
# 		SELECT stc.parent AS sales_invoice, stc.account_head, stc.base_tax_amount
# 		FROM `tabSales Taxes and Charges` stc
# 		INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
# 		WHERE si.docstatus = 1 AND stc.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	income_accounts = sorted({r.income_account for r in items if r.income_account})
# 	tax_accounts = sorted({r.account_head for r in taxes if r.account_head})

# 	item_map = {}
# 	for r in items:
# 		item_map.setdefault(r.sales_invoice, []).append(r)

# 	tax_map = {}
# 	for r in taxes:
# 		tax_map.setdefault(r.sales_invoice, []).append(r)

# 	data = []
# 	for h in headers:
# 		row = {
# 			"voucher_type": "Sales Invoice",
# 			"sales_invoice": h.sales_invoice,
# 			"posting_date": h.posting_date,
# 			"customer": h.customer,
# 			"receivable_account": h.receivable_account,
# 			"vat_emirate": h.vat_emirate,
# 		}
# 		for acc in income_accounts:
# 			row[_account_fieldname(acc)] = 0
# 		for acc in tax_accounts:
# 			row[_account_fieldname(acc)] = 0

# 		net_total = 0
# 		for it in item_map.get(h.sales_invoice, []):
# 			net_total += flt(it.base_net_amount)
# 			if it.income_account:
# 				row[_account_fieldname(it.income_account)] = flt(row[_account_fieldname(it.income_account)]) + flt(
# 					it.base_net_amount
# 				)

# 		tax_total = 0
# 		for t in tax_map.get(h.sales_invoice, []):
# 			tax_total += flt(t.base_tax_amount)
# 			if t.account_head:
# 				row[_account_fieldname(t.account_head)] = flt(row[_account_fieldname(t.account_head)]) + flt(
# 					t.base_tax_amount
# 				)

# 		row["net_total"] = flt(net_total)
# 		row["tax_total"] = flt(tax_total)
# 		row["grand_total"] = flt(net_total + tax_total)
# 		data.append(row)

# 	columns = _sales_breakdown_columns(income_accounts, tax_accounts)
# 	return columns, data


# def _sales_breakdown_columns(income_accounts, tax_accounts):
# 	columns = [
# 		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 110},
# 		{
# 			"fieldname": "sales_invoice",
# 			"label": _("Sales Invoice No"),
# 			"fieldtype": "Link",
# 			"options": "Sales Invoice",
# 			"width": 150,
# 		},
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{"fieldname": "vat_emirate", "label": _("VAT Emirates"), "fieldtype": "Data", "width": 140},
# 		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 220},
# 		{"fieldname": "receivable_account", "label": _("Receivable Account"), "fieldtype": "Data", "width": 220},
# 	]
# 	for acc in income_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	for acc in tax_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	columns.extend(
# 		[
# 			{"fieldname": "net_total", "label": _("Net Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "tax_total", "label": _("Tax Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 150},
# 		]
# 	)
# 	return columns


# # ------------------------------------------------------------------
# # Condition builders
# # ------------------------------------------------------------------


# def _si_conditions(company, from_date, to_date):
# 	cond = "AND si.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND si.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND si.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND si.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _pi_conditions(company, from_date, to_date):
# 	cond = "AND pi.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND pi.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND pi.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND pi.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _gl_conditions(company):
# 	cond = "AND gl.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND gl.account IN (SELECT account FROM `tabUAE VAT Account` WHERE parent = %s)"
# 		params.append(company)
# 	return cond, params


# # ------------------------------------------------------------------
# # Sales-side detail queries
# # ------------------------------------------------------------------


# def _rc_sales_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, SUM(gl.debit) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Purchase-side detail queries
# # ------------------------------------------------------------------


# def _std_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	cond += " AND pi.recoverable_standard_rated_expenses > 0"

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		WHERE 1=1 {cond}
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# def _rc_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' AND pi.recoverable_reverse_charge > 0 " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount,
# 		       SUM(gl.debit * pi.recoverable_reverse_charge / 100) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Combined detail queries
# # ------------------------------------------------------------------


# def _all_expenses_detail(company, from_date, to_date):
# 	data = []
# 	data.extend(_std_expenses_detail(company, from_date, to_date))
# 	data.extend(_rc_expenses_detail(company, from_date, to_date))
# 	return data


# # ==================================================================
# # Original helper functions
# # ==================================================================


# def get_total_emiratewise(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return frappe.db.sql(
# 			f"""
# 			select
# 				s.vat_emirate as emirate, sum(i.base_net_amount) as total, sum(i.tax_amount)
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and i.is_exempt != 1 and i.is_zero_rated != 1
# 				{conditions}
# 			group by
# 				s.vat_emirate;
# 			""",
# 			filters,
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_emirates():
# 	return ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]


# def get_filters(filters):
# 	query_filters = []
# 	if filters.get("company"):
# 		query_filters.append(["company", "=", filters["company"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", ">=", filters["from_date"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", "<=", filters["to_date"]])
# 	return query_filters


# def get_reverse_charge_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select sum(debit)  from
# 			`tabPurchase Invoice` p inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no =  p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_reverse_charge_recoverable_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["recoverable_reverse_charge", ">", "0"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_recoverable_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select
# 			sum(debit * p.recoverable_reverse_charge / 100)
# 		from
# 			`tabPurchase Invoice` p  inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no = p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and p.recoverable_reverse_charge > 0
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_conditions_join(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and p.company=%(company)s"),
# 		("from_date", " and p.posting_date>=%(from_date)s"),
# 		("to_date", " and p.posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# def get_standard_rated_expenses_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_standard_rated_expenses_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice",
# 				filters=query_filters,
# 				fields=["sum(recoverable_standard_rated_expenses)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice",
# 				filters=query_filters,
# 				fields=["sum(tourist_tax_return)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_zero_rated_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_zero_rated = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_exempt_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_exempt = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_conditions(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and company=%(company)s"),
# 		("from_date", " and posting_date>=%(from_date)s"),
# 		("to_date", " and posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# # ==================================================================
# # "See Transactions" review screen + automatic VAT Journal Entry
# # ==================================================================

# # VAT accounts used for the VAT Journal Entry.
# # Every company has its own chart of accounts, so we only store the ACCOUNT NUMBER here
# # (same number in all companies). The real account is looked up for the company selected
# # in the report, e.g. 213000 -> "213000 - Output VAT - OBR" for Orion Bus Rental.
# VAT_ACCOUNT_NUMBERS = {
# 	"output_vat": "213000",
# 	"output_vat_rcm": "213500",
# 	"input_vat": "118000",
# 	"input_vat_rcm": "185000",
# 	"vat_payable": "218010",
# 	"vat_receivable": "118500",
# }

# VAT_ACCOUNT_LABELS = {
# 	"output_vat": "Output VAT",
# 	"output_vat_rcm": "Output VAT RCM",
# 	"input_vat": "Input VAT",
# 	"input_vat_rcm": "Input VAT RCM",
# 	"vat_payable": "VAT Payable",
# 	"vat_receivable": "VAT Receivable",
# }


# def _vat_accounts(company):
# 	"""Returns {"output_vat": "<full account name of THIS company>", ...}."""
# 	accounts, missing = {}, []
# 	abbr = frappe.get_cached_value("Company", company, "abbr")
# 	for key, number in VAT_ACCOUNT_NUMBERS.items():
# 		name = frappe.db.get_value(
# 			"Account", {"company": company, "account_number": number, "is_group": 0}, "name"
# 		)
# 		if not name:  # fallback: "<number> - <label> - <abbr>"
# 			guess = "{0} - {1} - {2}".format(number, VAT_ACCOUNT_LABELS[key], abbr)
# 			if frappe.db.exists("Account", {"name": guess, "company": company, "is_group": 0}):
# 				name = guess
# 		if name:
# 			accounts[key] = name
# 		else:
# 			missing.append("{0} ({1})".format(number, VAT_ACCOUNT_LABELS[key]))
# 	if missing:
# 		frappe.throw(
# 			_("{0} does not have these VAT accounts: {1}. Create them (account number must match) and try again.").format(
# 				company, ", ".join(missing)
# 			)
# 		)
# 	return accounts


# # First line of the Journal Entry remark. Used to find which vouchers were already filed.
# VAT_JE_MARKER = "UAE VAT 201 |"
# VAT_SETTLE_MARKER = "UAE VAT 201 Settlement |"


# def _all_vat_rows(company, from_date, to_date):
# 	periods = (
# 		("current", from_date, to_date),
# 		("previous", add_months(from_date, -3), add_days(from_date, -1)),
# 	)
# 	rows = []
# 	for section, start, end in periods:
# 		for r in _collect_vat_transactions(company, start, end):
# 			r["section"] = section
# 			r["key"] = "{0}|{1}".format(r["category"], r["doc_name"])
# 			rows.append(r)
# 	return rows


# def get_vat_transactions(filters):
# 	"""Transactions for the VAT 201 screen.
# 	Section 'current'  : ALL transactions in the selected period (flagged ones are locked).
# 	Section 'previous' : transactions of the 3 months before the period that are NOT yet
# 	                     flagged custom_vat_filed (Sales and Purchase)."""
# 	company = filters.get("company")
# 	_check_filed_field()
# 	all_rows = _all_vat_rows(company, getdate(filters.get("from_date")), getdate(filters.get("to_date")))
# 	filed = _filed_vouchers(all_rows)

# 	rows = []
# 	for r in all_rows:
# 		r["locked"] = (r["doc_type"], r["doc_name"]) in filed
# 		if r["section"] == "previous":
# 			if r["locked"]:
# 				continue  # already filed in an earlier return -> do not show again
# 			r["note"] = _("Not previously reported")
# 		else:
# 			r["note"] = _("Already filed in a previous VAT return") if r["locked"] else ""
# 		rows.append(r)

# 	columns = [
# 		{"fieldname": "section", "label": _("Section"), "fieldtype": "Data", "width": 90},
# 		{"fieldname": "doc_name", "label": _("Document No"), "fieldtype": "Data", "width": 160},
# 		{"fieldname": "vat", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 140},
# 	]
# 	return columns, rows


# def _sales_report_rows(company, start, end, kind):
# 	"""Sales invoices exactly as the original report counts them (one row per invoice)."""
# 	if kind == "standard":
# 		item_cond = "i.is_exempt != 1 AND i.is_zero_rated != 1 AND s.vat_emirate IN %(emirates)s"
# 	elif kind == "zero":
# 		item_cond = "i.is_zero_rated = 1"
# 	else:
# 		item_cond = "i.is_exempt = 1"

# 	company_cond = " AND s.company = %(company)s" if company else ""
# 	return frappe.db.sql(
# 		f"""
# 		SELECT s.name AS doc_name, s.posting_date, s.customer_name AS party,
# 		       SUM(i.base_net_amount) AS amount, SUM(i.tax_amount) AS vat
# 		FROM `tabSales Invoice Item` i
# 		INNER JOIN `tabSales Invoice` s ON i.parent = s.name
# 		WHERE s.docstatus = 1 AND {item_cond}
# 		  AND s.posting_date >= %(start)s AND s.posting_date <= %(end)s
# 		  {company_cond}
# 		GROUP BY s.name
# 		ORDER BY s.posting_date
# 		""",
# 		{"company": company, "start": start, "end": end, "emirates": tuple(get_emirates())},
# 		as_dict=True,
# 	)


# def _collect_vat_transactions(company, start, end):
# 	out = []

# 	def add(doc_type, doc_name, posting_date, party, vtype, category, bucket, amount, vat):
# 		out.append(
# 			{
# 				"doc_type": doc_type,
# 				"doc_name": doc_name,
# 				"posting_date": str(posting_date),
# 				"party": party or "",
# 				"type": vtype,  # Sales = output VAT, Purchase = input VAT
# 				"category": category,
# 				"bucket": bucket,  # which VAT account this belongs to
# 				"amount": flt(amount),
# 				"vat": flt(vat),
# 			}
# 		)

# 	# Sales invoices - same rules as the original report's rows 1a-1g, 4 and 5:
# 	#  * Standard rated: items not zero-rated/exempt, and the invoice has a VAT Emirate set
# 	#    (VAT = sum of the item tax_amount, exactly like the summary)
# 	#  * Zero rated / Exempt: items flagged zero-rated / exempt (no VAT)
# 	for category, kind in (
# 		(_("Standard rated"), "standard"),
# 		(_("Zero rated"), "zero"),
# 		(_("Exempt"), "exempt"),
# 	):
# 		for d in _sales_report_rows(company, start, end, kind):
# 			add("Sales Invoice", d.doc_name, d.posting_date, d.party,
# 				"Sales", category, "output_vat", d.amount, d.vat if kind == "standard" else 0)

# 	# Tourist refunds (negative output VAT)
# 	tourist_filters = [
# 		["docstatus", "=", 1],
# 		["posting_date", "between", [start, end]],
# 		["tourist_tax_return", ">", 0],
# 	]
# 	if company:
# 		tourist_filters.append(["company", "=", company])
# 	for d in frappe.get_all(
# 		"Sales Invoice",
# 		filters=tourist_filters,
# 		fields=["name", "posting_date", "customer_name", "base_total", "tourist_tax_return"],
# 	):
# 		add("Sales Invoice", d.name, d.posting_date, d.customer_name, "Sales",
# 			_("Tourist refund"), "output_vat", -flt(d.base_total), -flt(d.tourist_tax_return))

# 	# Reverse charge - output side
# 	for d in _rc_sales_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Sales",
# 			_("Reverse charge (output)"), "output_vat_rcm", d.amount, d.vat_amount)

# 	# Purchases - input side
# 	for d in _std_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Standard rated expense"), "input_vat", d.amount, d.vat_amount)

# 	for d in _rc_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Reverse charge (input)"), "input_vat_rcm", d.amount, d.vat_amount)

# 	return sorted(out, key=lambda r: (r["posting_date"], r["doc_name"]))


# VAT_FILED_FIELD = "custom_vat_filed"  # Check field on Sales Invoice and Purchase Invoice
# MARK_FILED_ON_JE = True  # tick custom_vat_filed on the selected vouchers when the Journal Entry is created


# def _check_filed_field():
# 	missing = [
# 		dt for dt in ("Sales Invoice", "Purchase Invoice") if not frappe.get_meta(dt).has_field(VAT_FILED_FIELD)
# 	]
# 	if missing:
# 		frappe.throw(
# 			_("Please add a Check field named {0} to: {1}").format(VAT_FILED_FIELD, ", ".join(missing))
# 		)


# def _filed_vouchers(rows):
# 	"""Set of (doctype, name) that already have custom_vat_filed ticked."""
# 	filed = set()
# 	for dt in ("Sales Invoice", "Purchase Invoice"):
# 		names = list({r["doc_name"] for r in rows if r["doc_type"] == dt})
# 		if names:
# 			for n in frappe.get_all(dt, filters={"name": ["in", names], VAT_FILED_FIELD: 1}, pluck="name"):
# 				filed.add((dt, n))
# 	return filed


# def _build_vat_lines(totals, accounts):
# 	"""Journal Entry lines in two blocks, exactly like the accountant's format:

# 	  Output VAT            Dr
# 	  Output VAT RCM        Dr
# 	      VAT Payable             Cr   (total of the output block)

# 	  Input VAT                   Cr
# 	  Input VAT RCM               Cr
# 	  VAT Payable           Dr         (total of the input block)

# 	The two VAT Payable lines net to the VAT payable for the period. If input VAT is more
# 	than output VAT (refund), the part of the input block that cannot be set against
# 	output VAT is debited to VAT Receivable instead of VAT Payable."""
# 	lines = []

# 	def add(key, dr=0.0, cr=0.0):
# 		line = {"account": accounts[key]}
# 		if dr:
# 			line["debit_in_account_currency"] = dr
# 		if cr:
# 			line["credit_in_account_currency"] = cr
# 		lines.append(line)

# 	# ---- Block 1: output VAT (credit balance accounts -> debit to clear)
# 	out_net = 0.0  # debits minus credits of the block
# 	for key in ("output_vat", "output_vat_rcm"):
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			add(key, dr=amt)
# 		elif amt < 0:
# 			add(key, cr=-amt)
# 		out_net += amt
# 	out_net = flt(out_net, 2)

# 	# ---- Block 2: input VAT (debit balance accounts -> credit to clear)
# 	in_net = 0.0  # credits minus debits of the block
# 	for key in ("input_vat", "input_vat_rcm"):
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			add(key, cr=amt)
# 		elif amt < 0:
# 			add(key, dr=-amt)
# 		in_net += amt
# 	in_net = flt(in_net, 2)

# 	net = flt(out_net - in_net, 2)  # > 0 payable, < 0 receivable

# 	# VAT Payable line of the output block goes right after the output lines
# 	# (credit when output > 0), then the input block lines, then its VAT Payable line.
# 	out_lines = [l for l in lines if l["account"] in (accounts["output_vat"], accounts["output_vat_rcm"])]
# 	in_lines = [l for l in lines if l["account"] in (accounts["input_vat"], accounts["input_vat_rcm"])]
# 	lines = list(out_lines)
# 	if out_net > 0:
# 		add("vat_payable", cr=out_net)
# 	elif out_net < 0:
# 		add("vat_payable", dr=-out_net)
# 	lines.extend(in_lines)

# 	if in_net > 0:
# 		if net >= 0:
# 			add("vat_payable", dr=in_net)
# 		else:
# 			# refund: only the part matching output VAT can reduce VAT Payable
# 			set_off = max(out_net, 0.0)
# 			if set_off:
# 				add("vat_payable", dr=set_off)
# 			add("vat_receivable", dr=flt(in_net - set_off, 2))
# 	elif in_net < 0:
# 		add("vat_payable", cr=-in_net)
# 	return lines, net


# def _check_accounts(accounts):
# 	missing = [a for a in accounts if not frappe.db.exists("Account", a)]
# 	if missing:
# 		frappe.throw(
# 			_("These accounts were not found: {0}. Create them (VAT Receivable goes under Current Assets) "
# 			"or correct VAT_ACCOUNT_NUMBERS in the report's Python file.").format(
# 				", ".join(missing)
# 			)
# 		)


# @frappe.whitelist()
# def create_vat_journal_entry(company, from_date, to_date, keys):
# 	"""Creates ONE draft Journal Entry for the selected transactions."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	keys = json.loads(keys) if isinstance(keys, str) else keys
# 	if not keys:
# 		frappe.throw(_("Please select at least one transaction."))

# 	from_date, to_date = getdate(from_date), getdate(to_date)
# 	rows = {r["key"]: r for r in _all_vat_rows(company, from_date, to_date)}

# 	selected = []
# 	for k in keys:
# 		if k not in rows:
# 			frappe.throw(_("{0} is no longer available for this return. Please reload and select again.").format(k))
# 		selected.append(rows[k])

# 	_check_filed_field()
# 	filed = _filed_vouchers(selected)
# 	already = sorted({r["doc_name"] for r in selected if (r["doc_type"], r["doc_name"]) in filed})
# 	if already:
# 		frappe.throw(_("Already included in another return: {0}").format(", ".join(already)))

# 	totals = {}
# 	for r in selected:
# 		totals[r["bucket"]] = totals.get(r["bucket"], 0) + r["vat"]

# 	accounts = _vat_accounts(company)
# 	lines, net = _build_vat_lines(totals, accounts)
# 	if not lines:
# 		frappe.throw(_("The selected transactions have no VAT amount to post."))
# 	_check_accounts([l["account"] for l in lines])

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Journal Entry"
# 	je.company = company
# 	je.posting_date = to_date
# 	je.user_remark = "{0} {1} | {2} to {3}\nVouchers: {4}".format(
# 		VAT_JE_MARKER,
# 		company,
# 		from_date,
# 		to_date,
# 		", ".join(sorted({r["doc_name"] for r in selected})),
# 	)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()  # stays in Draft so the accountant can review and submit

# 	if MARK_FILED_ON_JE:
# 		for dt, name in {(r["doc_type"], r["doc_name"]) for r in selected}:
# 			frappe.db.set_value(dt, name, VAT_FILED_FIELD, 1, update_modified=False)

# 	output = sum(flt(totals.get(k, 0)) for k in ("output_vat", "output_vat_rcm"))
# 	inp = sum(flt(totals.get(k, 0)) for k in ("input_vat", "input_vat_rcm"))
# 	return {
# 		"name": je.name,
# 		"output": flt(output, 2),
# 		"input": flt(inp, 2),
# 		"net": net,  # > 0 payable, < 0 receivable
# 	}


# @frappe.whitelist()
# def create_vat_settlement_entry(journal_entry, bank_account, posting_date, reference_no, reference_date):
# 	"""Payment of VAT Payable (Dr Payable, Cr Bank) or receipt of a VAT refund
# 	(Dr Bank, Cr Receivable) as a draft Bank Entry."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	src = frappe.get_doc("Journal Entry", journal_entry)
# 	if not (src.user_remark or "").startswith(VAT_JE_MARKER) or src.docstatus == 2:
# 		frappe.throw(_("{0} is not a valid VAT Journal Entry.").format(journal_entry))

# 	marker = "{0} {1}".format(VAT_SETTLE_MARKER, src.name)
# 	if frappe.db.exists(
# 		"Journal Entry", {"docstatus": ["<", 2], "user_remark": ["like", marker + "%"]}
# 	):
# 		frappe.throw(_("A payment/refund entry already exists for {0}.").format(src.name))

# 	accounts = _vat_accounts(src.company)
# 	if frappe.db.get_value("Account", bank_account, "company") != src.company:
# 		frappe.throw(_("{0} does not belong to {1}.").format(bank_account, src.company))

# 	payable = sum(
# 		flt(r.credit_in_account_currency) - flt(r.debit_in_account_currency)
# 		for r in src.accounts
# 		if r.account == accounts["vat_payable"]
# 	)
# 	receivable = sum(
# 		flt(r.debit_in_account_currency) - flt(r.credit_in_account_currency)
# 		for r in src.accounts
# 		if r.account == accounts["vat_receivable"]
# 	)

# 	if payable > 0:
# 		amount = flt(payable, 2)
# 		lines = [
# 			{"account": accounts["vat_payable"], "debit_in_account_currency": amount},
# 			{"account": bank_account, "credit_in_account_currency": amount},
# 		]
# 	elif receivable > 0:
# 		amount = flt(receivable, 2)
# 		lines = [
# 			{"account": bank_account, "debit_in_account_currency": amount},
# 			{"account": accounts["vat_receivable"], "credit_in_account_currency": amount},
# 		]
# 	else:
# 		frappe.throw(_("There is no VAT payable or receivable to settle in {0}.").format(src.name))

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Bank Entry"
# 	je.company = src.company
# 	je.posting_date = getdate(posting_date)
# 	je.cheque_no = reference_no
# 	je.cheque_date = getdate(reference_date)
# 	je.user_remark = "{0}\nVAT payment/refund for {1}".format(marker, src.name)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()
# 	return je.name




# ################################################
# import json
# import re

# import frappe
# from frappe import _
# from frappe.utils import add_days, add_months, flt, getdate


# def execute(filters=None):
# 	filters = filters or {}
# 	if not filters.get("company"):  # first page load runs the report with empty filters
# 		return get_columns(), []
# 	if filters.get("drilldown_key") == "vat_transactions":
# 		return get_vat_transactions(filters)
# 	if filters.get("drilldown_key"):
# 		return get_drilldown(filters)
# 	columns = get_columns()
# 	data, emirates, amounts_by_emirate = get_data(filters)
# 	return columns, data


# # ------------------------------------------------------------------
# # Summary columns
# # ------------------------------------------------------------------


# def get_columns():
# 	return [
# 		{"fieldname": "no", "label": _("No"), "fieldtype": "Data", "width": 50},
# 		{"fieldname": "legend", "label": _("Legend"), "fieldtype": "Data", "width": 300},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 125},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# # ------------------------------------------------------------------
# # Summary data
# # ------------------------------------------------------------------


# def get_data(filters=None):
# 	data = []
# 	emirates, amounts_by_emirate = append_vat_on_sales(data, filters)
# 	append_vat_on_expenses(data, filters)
# 	return data, emirates, amounts_by_emirate


# def append_vat_on_sales(data, filters):
# 	append_data(data, "", _("VAT on Sales and All Other Outputs"), "", "")

# 	emirates, amounts_by_emirate = standard_rated_expenses_emiratewise(data, filters)

# 	total_amounts = [amounts_by_emirate.get(e, {}).get("raw_amount", 0) for e in emirates]
# 	total_vat_amounts = [amounts_by_emirate.get(e, {}).get("raw_vat_amount", 0) for e in emirates]

# 	tourist_total = get_tourist_tax_return_total(filters)
# 	tourist_tax = get_tourist_tax_return_tax(filters)
# 	append_data(
# 		data,
# 		"2",
# 		_("Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme"),
# 		frappe.format((-1) * tourist_total, "Currency"),
# 		frappe.format((-1) * tourist_tax, "Currency"),
# 		drilldown_key="tourist_refund",
# 		raw_amount=(-1) * tourist_total,
# 		raw_vat_amount=(-1) * tourist_tax,
# 	)
# 	total_amounts.append((-1) * tourist_total)
# 	total_vat_amounts.append((-1) * tourist_tax)

# 	rc_total = get_reverse_charge_total(filters)
# 	rc_tax = get_reverse_charge_tax(filters)
# 	append_data(
# 		data,
# 		"3",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_total, "Currency"),
# 		frappe.format(rc_tax, "Currency"),
# 		drilldown_key="reverse_charge_sales",
# 		raw_amount=rc_total,
# 		raw_vat_amount=rc_tax,
# 	)
# 	total_amounts.append(rc_total)
# 	total_vat_amounts.append(rc_tax)

# 	zero_total = get_zero_rated_total(filters)
# 	append_data(
# 		data,
# 		"4",
# 		_("Zero Rated"),
# 		frappe.format(zero_total, "Currency"),
# 		"-",
# 		drilldown_key="zero_rated",
# 		raw_amount=zero_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(zero_total)

# 	exempt_total = get_exempt_total(filters)
# 	append_data(
# 		data,
# 		"5",
# 		_("Exempt Supplies"),
# 		frappe.format(exempt_total, "Currency"),
# 		"-",
# 		drilldown_key="exempt",
# 		raw_amount=exempt_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(exempt_total)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Sales and All Other Outputs"),
# 		frappe.format(sum(total_amounts), "Currency"),
# 		frappe.format(sum(total_vat_amounts), "Currency"),
# 	)

# 	append_data(data, "", "", "", "")

# 	return emirates, amounts_by_emirate


# def standard_rated_expenses_emiratewise(data, filters):
# 	total_emiratewise = get_total_emiratewise(filters)
# 	emirates = get_emirates()
# 	amounts_by_emirate = {}
# 	for emirate, amount, vat in total_emiratewise:
# 		amounts_by_emirate[emirate] = {
# 			"legend": emirate,
# 			"raw_amount": flt(amount),
# 			"raw_vat_amount": flt(vat),
# 			"amount": frappe.format(amount, "Currency"),
# 			"vat_amount": frappe.format(vat, "Currency"),
# 		}
# 	amounts_by_emirate = append_emiratewise_expenses(data, emirates, amounts_by_emirate)
# 	return emirates, amounts_by_emirate


# def append_emiratewise_expenses(data, emirates, amounts_by_emirate):
# 	for no, emirate in enumerate(emirates, 97):
# 		key = "standard_rated_{0}".format(emirate)
# 		if emirate in amounts_by_emirate:
# 			amounts_by_emirate[emirate]["no"] = _("1{0}").format(chr(no))
# 			amounts_by_emirate[emirate]["legend"] = _("Standard rated supplies in {0}").format(emirate)
# 			amounts_by_emirate[emirate]["drilldown_key"] = key
# 			data.append(amounts_by_emirate[emirate])
# 		else:
# 			append_data(
# 				data,
# 				_("1{0}").format(chr(no)),
# 				_("Standard rated supplies in {0}").format(emirate),
# 				frappe.format(0, "Currency"),
# 				frappe.format(0, "Currency"),
# 				drilldown_key=key,
# 				raw_amount=0,
# 				raw_vat_amount=0,
# 			)
# 	return amounts_by_emirate


# def append_vat_on_expenses(data, filters):
# 	append_data(data, "", _("VAT on Expenses and All Other Inputs"), "", "")

# 	std_exp_total = get_standard_rated_expenses_total(filters)
# 	std_exp_tax = get_standard_rated_expenses_tax(filters)
# 	append_data(
# 		data,
# 		"9",
# 		_("Standard Rated Expenses"),
# 		frappe.format(std_exp_total, "Currency"),
# 		frappe.format(std_exp_tax, "Currency"),
# 		drilldown_key="standard_rated_expenses",
# 		raw_amount=std_exp_total,
# 		raw_vat_amount=std_exp_tax,
# 	)

# 	rc_rec_total = get_reverse_charge_recoverable_total(filters)
# 	rc_rec_tax = get_reverse_charge_recoverable_tax(filters)
# 	append_data(
# 		data,
# 		"10",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_rec_total, "Currency"),
# 		frappe.format(rc_rec_tax, "Currency"),
# 		drilldown_key="reverse_charge_expenses",
# 		raw_amount=rc_rec_total,
# 		raw_vat_amount=rc_rec_tax,
# 	)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Expenses and All Other Inputs"),
# 		frappe.format(std_exp_total + rc_rec_total, "Currency"),
# 		frappe.format(std_exp_tax + rc_rec_tax, "Currency"),
# 	)


# def append_data(data, no, legend, amount, vat_amount, drilldown_key=None, raw_amount=0, raw_vat_amount=0):
# 	row = {"no": no, "legend": legend, "amount": amount, "vat_amount": vat_amount}
# 	if drilldown_key:
# 		row["drilldown_key"] = drilldown_key
# 		row["raw_amount"] = raw_amount
# 		row["raw_vat_amount"] = raw_vat_amount
# 	data.append(row)


# # ==================================================================
# # Drill-down
# # ==================================================================


# def get_drilldown(filters):
# 	key = filters.get("drilldown_key")
# 	company = filters.get("company")
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")

# 	purchase_keys = ("standard_rated_expenses", "reverse_charge_expenses", "expenses_total")
# 	if key in purchase_keys:
# 		columns, data = _get_purchase_detail(key, company, from_date, to_date)
# 	elif key == "reverse_charge_sales":
# 		columns = _purchase_detail_columns()
# 		data = _rc_sales_detail(company, from_date, to_date)
# 	else:
# 		columns, data = _get_sales_detail(key, company, from_date, to_date)

# 	return columns, data, None, None, None, True


# def _get_sales_detail(key, company, from_date, to_date):
# 	if key.startswith("standard_rated_"):
# 		emirate = key[len("standard_rated_") :]
# 		return _sales_invoice_breakdown(company, from_date, to_date, emirate=emirate)
# 	elif key == "tourist_refund":
# 		return _sales_invoice_breakdown(company, from_date, to_date, tourist_only=True)
# 	elif key == "zero_rated":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_zero_rated=True)
# 	elif key == "exempt":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_exempt=True)
# 	elif key == "sales_total":
# 		return _sales_invoice_breakdown(company, from_date, to_date)
# 	return [], []


# def _get_purchase_detail(key, company, from_date, to_date):
# 	columns = _purchase_detail_columns()
# 	if key == "standard_rated_expenses":
# 		data = _std_expenses_detail(company, from_date, to_date)
# 	elif key == "reverse_charge_expenses":
# 		data = _rc_expenses_detail(company, from_date, to_date)
# 	elif key == "expenses_total":
# 		data = _all_expenses_detail(company, from_date, to_date)
# 	else:
# 		data = []
# 	return columns, data


# def _purchase_detail_columns():
# 	return [
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{
# 			"fieldname": "doc_name",
# 			"label": _("Document No"),
# 			"fieldtype": "Dynamic Link",
# 			"options": "doc_type",
# 			"width": 180,
# 		},
# 		{"fieldname": "party", "label": _("Party"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "item", "label": _("Item"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 130},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# def _account_fieldname(account):
# 	"""Sanitize an account name for use as a column fieldname."""
# 	return "acc_" + re.sub(r"[^a-zA-Z0-9_]", "_", account)


# def _sales_invoice_breakdown(
# 	company, from_date, to_date, emirate=None, is_zero_rated=False, is_exempt=False, tourist_only=False
# ):
# 	"""Account-wise breakdown of qualifying Sales Invoices."""
# 	si_cond, si_params = _si_conditions(company, from_date, to_date)

# 	if tourist_only:
# 		invoices = frappe.db.sql_list(
# 			"SELECT si.name FROM `tabSales Invoice` si WHERE 1=1 "
# 			+ si_cond + " AND si.tourist_tax_return > 0",
# 			tuple(si_params),
# 		)
# 	else:
# 		item_cond = ""
# 		item_params = []
# 		if emirate:
# 			item_cond += " AND si.vat_emirate = %s"
# 			item_params.append(emirate)
# 		if is_zero_rated:
# 			item_cond += " AND sii.is_zero_rated = 1"
# 		elif is_exempt:
# 			item_cond += " AND sii.is_exempt = 1"
# 		else:
# 			item_cond += " AND sii.is_exempt != 1 AND sii.is_zero_rated != 1"

# 		invoices = frappe.db.sql_list(
# 			"SELECT DISTINCT si.name FROM `tabSales Invoice Item` sii "
# 			"INNER JOIN `tabSales Invoice` si ON si.name = sii.parent "
# 			"WHERE 1=1 " + si_cond + item_cond,
# 			tuple(si_params + item_params),
# 		)

# 	if not invoices:
# 		return _sales_breakdown_columns([], []), []

# 	invoices_tuple = tuple(invoices)

# 	headers = frappe.db.sql(
# 		"""
# 		SELECT si.name AS sales_invoice, si.posting_date, si.customer_name AS customer,
# 		       si.debit_to AS receivable_account, si.vat_emirate
# 		FROM `tabSales Invoice` si
# 		WHERE si.docstatus = 1 AND si.name IN %s
# 		ORDER BY si.posting_date
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	items = frappe.db.sql(
# 		"""
# 		SELECT sii.parent AS sales_invoice, sii.income_account, sii.base_net_amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# 		WHERE si.docstatus = 1 AND sii.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	taxes = frappe.db.sql(
# 		"""
# 		SELECT stc.parent AS sales_invoice, stc.account_head, stc.base_tax_amount
# 		FROM `tabSales Taxes and Charges` stc
# 		INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
# 		WHERE si.docstatus = 1 AND stc.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	income_accounts = sorted({r.income_account for r in items if r.income_account})
# 	tax_accounts = sorted({r.account_head for r in taxes if r.account_head})

# 	item_map = {}
# 	for r in items:
# 		item_map.setdefault(r.sales_invoice, []).append(r)

# 	tax_map = {}
# 	for r in taxes:
# 		tax_map.setdefault(r.sales_invoice, []).append(r)

# 	data = []
# 	for h in headers:
# 		row = {
# 			"voucher_type": "Sales Invoice",
# 			"sales_invoice": h.sales_invoice,
# 			"posting_date": h.posting_date,
# 			"customer": h.customer,
# 			"receivable_account": h.receivable_account,
# 			"vat_emirate": h.vat_emirate,
# 		}
# 		for acc in income_accounts:
# 			row[_account_fieldname(acc)] = 0
# 		for acc in tax_accounts:
# 			row[_account_fieldname(acc)] = 0

# 		net_total = 0
# 		for it in item_map.get(h.sales_invoice, []):
# 			net_total += flt(it.base_net_amount)
# 			if it.income_account:
# 				row[_account_fieldname(it.income_account)] = flt(row[_account_fieldname(it.income_account)]) + flt(
# 					it.base_net_amount
# 				)

# 		tax_total = 0
# 		for t in tax_map.get(h.sales_invoice, []):
# 			tax_total += flt(t.base_tax_amount)
# 			if t.account_head:
# 				row[_account_fieldname(t.account_head)] = flt(row[_account_fieldname(t.account_head)]) + flt(
# 					t.base_tax_amount
# 				)

# 		row["net_total"] = flt(net_total)
# 		row["tax_total"] = flt(tax_total)
# 		row["grand_total"] = flt(net_total + tax_total)
# 		data.append(row)

# 	columns = _sales_breakdown_columns(income_accounts, tax_accounts)
# 	return columns, data


# def _sales_breakdown_columns(income_accounts, tax_accounts):
# 	columns = [
# 		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 110},
# 		{
# 			"fieldname": "sales_invoice",
# 			"label": _("Sales Invoice No"),
# 			"fieldtype": "Link",
# 			"options": "Sales Invoice",
# 			"width": 150,
# 		},
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{"fieldname": "vat_emirate", "label": _("VAT Emirates"), "fieldtype": "Data", "width": 140},
# 		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 220},
# 		{"fieldname": "receivable_account", "label": _("Receivable Account"), "fieldtype": "Data", "width": 220},
# 	]
# 	for acc in income_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	for acc in tax_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	columns.extend(
# 		[
# 			{"fieldname": "net_total", "label": _("Net Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "tax_total", "label": _("Tax Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 150},
# 		]
# 	)
# 	return columns


# # ------------------------------------------------------------------
# # Condition builders
# # ------------------------------------------------------------------


# def _si_conditions(company, from_date, to_date):
# 	cond = "AND si.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND si.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND si.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND si.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _pi_conditions(company, from_date, to_date):
# 	cond = "AND pi.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND pi.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND pi.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND pi.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _gl_conditions(company):
# 	cond = "AND gl.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND gl.account IN (SELECT account FROM `tabUAE VAT Account` WHERE parent = %s)"
# 		params.append(company)
# 	return cond, params


# # ------------------------------------------------------------------
# # Sales-side detail queries
# # ------------------------------------------------------------------


# def _rc_sales_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, SUM(gl.debit) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Purchase-side detail queries
# # ------------------------------------------------------------------


# def _std_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	cond += " AND pi.recoverable_standard_rated_expenses > 0"

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		WHERE 1=1 {cond}
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# def _rc_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' AND pi.recoverable_reverse_charge > 0 " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount,
# 		       SUM(gl.debit * pi.recoverable_reverse_charge / 100) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Combined detail queries
# # ------------------------------------------------------------------


# def _all_expenses_detail(company, from_date, to_date):
# 	data = []
# 	data.extend(_std_expenses_detail(company, from_date, to_date))
# 	data.extend(_rc_expenses_detail(company, from_date, to_date))
# 	return data


# # ==================================================================
# # Original helper functions
# # ==================================================================


# def get_total_emiratewise(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return frappe.db.sql(
# 			f"""
# 			select
# 				s.vat_emirate as emirate, sum(i.base_net_amount) as total, sum(i.tax_amount)
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and i.is_exempt != 1 and i.is_zero_rated != 1
# 				{conditions}
# 			group by
# 				s.vat_emirate;
# 			""",
# 			filters,
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_emirates():
# 	return ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]


# def get_filters(filters):
# 	query_filters = []
# 	if filters.get("company"):
# 		query_filters.append(["company", "=", filters["company"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", ">=", filters["from_date"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", "<=", filters["to_date"]])
# 	return query_filters


# def get_reverse_charge_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select sum(debit)  from
# 			`tabPurchase Invoice` p inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no =  p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_reverse_charge_recoverable_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["recoverable_reverse_charge", ">", "0"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_recoverable_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select
# 			sum(debit * p.recoverable_reverse_charge / 100)
# 		from
# 			`tabPurchase Invoice` p  inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no = p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and p.recoverable_reverse_charge > 0
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_conditions_join(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and p.company=%(company)s"),
# 		("from_date", " and p.posting_date>=%(from_date)s"),
# 		("to_date", " and p.posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# def get_standard_rated_expenses_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_standard_rated_expenses_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice",
# 				filters=query_filters,
# 				fields=["sum(recoverable_standard_rated_expenses)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice",
# 				filters=query_filters,
# 				fields=["sum(tourist_tax_return)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_zero_rated_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_zero_rated = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_exempt_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_exempt = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_conditions(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and company=%(company)s"),
# 		("from_date", " and posting_date>=%(from_date)s"),
# 		("to_date", " and posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# # ==================================================================
# # "See Transactions" review screen + automatic VAT Journal Entry
# # ==================================================================

# # VAT accounts used for the VAT Journal Entry.
# # Every company has its own chart of accounts, so we only store the ACCOUNT NUMBER here
# # (same number in all companies). The real account is looked up for the company selected
# # in the report, e.g. 213000 -> "213000 - Output VAT - OBR" for Orion Bus Rental.
# VAT_ACCOUNT_NUMBERS = {
# 	"output_vat": "213000",
# 	"output_vat_rcm": "213500",
# 	"input_vat": "118000",
# 	"input_vat_rcm": "185000",
# 	"vat_payable": "218010",
# }

# VAT_ACCOUNT_LABELS = {
# 	"output_vat": "Output VAT",
# 	"output_vat_rcm": "Output VAT RCM",
# 	"input_vat": "Input VAT",
# 	"input_vat_rcm": "Input VAT RCM",
# 	"vat_payable": "VAT Payable",
# }


# def _vat_accounts(company):
# 	"""Returns {"output_vat": "<full account name of THIS company>", ...}."""
# 	accounts, missing = {}, []
# 	abbr = frappe.get_cached_value("Company", company, "abbr")
# 	for key, number in VAT_ACCOUNT_NUMBERS.items():
# 		name = frappe.db.get_value(
# 			"Account", {"company": company, "account_number": number, "is_group": 0}, "name"
# 		)
# 		if not name:  # fallback: "<number> - <label> - <abbr>"
# 			guess = "{0} - {1} - {2}".format(number, VAT_ACCOUNT_LABELS[key], abbr)
# 			if frappe.db.exists("Account", {"name": guess, "company": company, "is_group": 0}):
# 				name = guess
# 		if name:
# 			accounts[key] = name
# 		else:
# 			missing.append("{0} ({1})".format(number, VAT_ACCOUNT_LABELS[key]))
# 	if missing:
# 		frappe.throw(
# 			_("{0} does not have these VAT accounts: {1}. Create them (account number must match) and try again.").format(
# 				company, ", ".join(missing)
# 			)
# 		)
# 	return accounts


# # First line of the Journal Entry remark. Used to find which vouchers were already filed.
# VAT_JE_MARKER = "UAE VAT 201 |"
# VAT_SETTLE_MARKER = "UAE VAT 201 Settlement |"


# def _all_vat_rows(company, from_date, to_date):
# 	periods = (
# 		("current", from_date, to_date),
# 		("previous", add_months(from_date, -3), add_days(from_date, -1)),
# 	)
# 	rows = []
# 	for section, start, end in periods:
# 		for r in _collect_vat_transactions(company, start, end):
# 			r["section"] = section
# 			r["key"] = "{0}|{1}".format(r["category"], r["doc_name"])
# 			rows.append(r)
# 	return rows


# def get_vat_transactions(filters):
# 	"""Transactions for the VAT 201 screen.
# 	Section 'current'  : ALL transactions in the selected period (flagged ones are locked).
# 	Section 'previous' : transactions of the 3 months before the period that are NOT yet
# 	                     flagged custom_vat_filed (Sales and Purchase)."""
# 	company = filters.get("company")
# 	_check_filed_field()
# 	all_rows = _all_vat_rows(company, getdate(filters.get("from_date")), getdate(filters.get("to_date")))
# 	filed = _filed_vouchers(all_rows)

# 	rows = []
# 	for r in all_rows:
# 		r["locked"] = (r["doc_type"], r["doc_name"]) in filed
# 		if r["section"] == "previous":
# 			if r["locked"]:
# 				continue  # already filed in an earlier return -> do not show again
# 			r["note"] = _("Not previously reported")
# 		else:
# 			r["note"] = _("Already filed in a previous VAT return") if r["locked"] else ""
# 		rows.append(r)

# 	columns = [
# 		{"fieldname": "section", "label": _("Section"), "fieldtype": "Data", "width": 90},
# 		{"fieldname": "doc_name", "label": _("Document No"), "fieldtype": "Data", "width": 160},
# 		{"fieldname": "vat", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 140},
# 	]
# 	return columns, rows


# def _sales_report_rows(company, start, end, kind):
# 	"""Sales invoices exactly as the original report counts them (one row per invoice)."""
# 	if kind == "standard":
# 		item_cond = "i.is_exempt != 1 AND i.is_zero_rated != 1 AND s.vat_emirate IN %(emirates)s"
# 	elif kind == "zero":
# 		item_cond = "i.is_zero_rated = 1"
# 	else:
# 		item_cond = "i.is_exempt = 1"

# 	company_cond = " AND s.company = %(company)s" if company else ""
# 	return frappe.db.sql(
# 		f"""
# 		SELECT s.name AS doc_name, s.posting_date, s.customer_name AS party,
# 		       SUM(i.base_net_amount) AS amount, SUM(i.tax_amount) AS vat
# 		FROM `tabSales Invoice Item` i
# 		INNER JOIN `tabSales Invoice` s ON i.parent = s.name
# 		WHERE s.docstatus = 1 AND {item_cond}
# 		  AND s.posting_date >= %(start)s AND s.posting_date <= %(end)s
# 		  {company_cond}
# 		GROUP BY s.name
# 		ORDER BY s.posting_date
# 		""",
# 		{"company": company, "start": start, "end": end, "emirates": tuple(get_emirates())},
# 		as_dict=True,
# 	)


# def _collect_vat_transactions(company, start, end):
# 	out = []

# 	def add(doc_type, doc_name, posting_date, party, vtype, category, bucket, amount, vat):
# 		out.append(
# 			{
# 				"doc_type": doc_type,
# 				"doc_name": doc_name,
# 				"posting_date": str(posting_date),
# 				"party": party or "",
# 				"type": vtype,  # Sales = output VAT, Purchase = input VAT
# 				"category": category,
# 				"bucket": bucket,  # which VAT account this belongs to
# 				"amount": flt(amount),
# 				"vat": flt(vat),
# 			}
# 		)

# 	# Sales invoices - same rules as the original report's rows 1a-1g, 4 and 5:
# 	#  * Standard rated: items not zero-rated/exempt, and the invoice has a VAT Emirate set
# 	#    (VAT = sum of the item tax_amount, exactly like the summary)
# 	#  * Zero rated / Exempt: items flagged zero-rated / exempt (no VAT)
# 	for category, kind in (
# 		(_("Standard rated"), "standard"),
# 		(_("Zero rated"), "zero"),
# 		(_("Exempt"), "exempt"),
# 	):
# 		for d in _sales_report_rows(company, start, end, kind):
# 			add("Sales Invoice", d.doc_name, d.posting_date, d.party,
# 				"Sales", category, "output_vat", d.amount, d.vat if kind == "standard" else 0)

# 	# Tourist refunds (negative output VAT)
# 	tourist_filters = [
# 		["docstatus", "=", 1],
# 		["posting_date", "between", [start, end]],
# 		["tourist_tax_return", ">", 0],
# 	]
# 	if company:
# 		tourist_filters.append(["company", "=", company])
# 	for d in frappe.get_all(
# 		"Sales Invoice",
# 		filters=tourist_filters,
# 		fields=["name", "posting_date", "customer_name", "base_total", "tourist_tax_return"],
# 	):
# 		add("Sales Invoice", d.name, d.posting_date, d.customer_name, "Sales",
# 			_("Tourist refund"), "output_vat", -flt(d.base_total), -flt(d.tourist_tax_return))

# 	# Reverse charge - output side
# 	for d in _rc_sales_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Sales",
# 			_("Reverse charge (output)"), "output_vat_rcm", d.amount, d.vat_amount)

# 	# Purchases - input side
# 	for d in _std_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Standard rated expense"), "input_vat", d.amount, d.vat_amount)

# 	for d in _rc_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Reverse charge (input)"), "input_vat_rcm", d.amount, d.vat_amount)

# 	return sorted(out, key=lambda r: (r["posting_date"], r["doc_name"]))


# VAT_FILED_FIELD = "custom_vat_filed"  # Check field on Sales Invoice and Purchase Invoice
# MARK_FILED_ON_JE = True  # tick custom_vat_filed on the selected vouchers when the Journal Entry is created


# def _check_filed_field():
# 	missing = [
# 		dt for dt in ("Sales Invoice", "Purchase Invoice") if not frappe.get_meta(dt).has_field(VAT_FILED_FIELD)
# 	]
# 	if missing:
# 		frappe.throw(
# 			_("Please add a Check field named {0} to: {1}").format(VAT_FILED_FIELD, ", ".join(missing))
# 		)


# def _filed_vouchers(rows):
# 	"""Set of (doctype, name) that already have custom_vat_filed ticked."""
# 	filed = set()
# 	for dt in ("Sales Invoice", "Purchase Invoice"):
# 		names = list({r["doc_name"] for r in rows if r["doc_type"] == dt})
# 		if names:
# 			for n in frappe.get_all(dt, filters={"name": ["in", names], VAT_FILED_FIELD: 1}, pluck="name"):
# 				filed.add((dt, n))
# 	return filed


# def _build_vat_lines(totals, accounts):
# 	"""Journal Entry lines in two blocks, exactly like the accountant's format:

# 	  Output VAT            Dr
# 	  Output VAT RCM        Dr
# 	      VAT Payable             Cr   (total of the output block)

# 	  Input VAT                   Cr
# 	  Input VAT RCM               Cr
# 	  VAT Payable           Dr         (total of the input block)

# 	The two VAT Payable lines net to the VAT payable for the period. There is no separate
# 	"VAT Receivable" account: if input VAT is more than output VAT, VAT Payable simply ends
# 	with a debit (negative) balance, i.e. a refund is due."""
# 	lines = []

# 	def add(key, dr=0.0, cr=0.0):
# 		line = {"account": accounts[key]}
# 		if dr:
# 			line["debit_in_account_currency"] = dr
# 		if cr:
# 			line["credit_in_account_currency"] = cr
# 		lines.append(line)

# 	# ---- Block 1: output VAT (credit balance accounts -> debit to clear)
# 	out_net = 0.0  # debits minus credits of the block
# 	for key in ("output_vat", "output_vat_rcm"):
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			add(key, dr=amt)
# 		elif amt < 0:
# 			add(key, cr=-amt)
# 		out_net += amt
# 	out_net = flt(out_net, 2)

# 	# ---- Block 2: input VAT (debit balance accounts -> credit to clear)
# 	in_net = 0.0  # credits minus debits of the block
# 	for key in ("input_vat", "input_vat_rcm"):
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			add(key, cr=amt)
# 		elif amt < 0:
# 			add(key, dr=-amt)
# 		in_net += amt
# 	in_net = flt(in_net, 2)

# 	net = flt(out_net - in_net, 2)  # > 0 payable, < 0 refundable (negative VAT Payable)

# 	# VAT Payable line of the output block goes right after the output lines
# 	# (credit when output > 0), then the input block lines, then its VAT Payable line.
# 	out_lines = [l for l in lines if l["account"] in (accounts["output_vat"], accounts["output_vat_rcm"])]
# 	in_lines = [l for l in lines if l["account"] in (accounts["input_vat"], accounts["input_vat_rcm"])]
# 	lines = list(out_lines)
# 	if out_net > 0:
# 		add("vat_payable", cr=out_net)
# 	elif out_net < 0:
# 		add("vat_payable", dr=-out_net)
# 	lines.extend(in_lines)

# 	if in_net > 0:
# 		add("vat_payable", dr=in_net)
# 	elif in_net < 0:
# 		add("vat_payable", cr=-in_net)
# 	return lines, net


# def _check_accounts(accounts):
# 	missing = [a for a in accounts if not frappe.db.exists("Account", a)]
# 	if missing:
# 		frappe.throw(
# 			_("These accounts were not found: {0}. Create them "
# 			"or correct VAT_ACCOUNT_NUMBERS in the report's Python file.").format(
# 				", ".join(missing)
# 			)
# 		)


# @frappe.whitelist()
# def create_vat_journal_entry(company, from_date, to_date, keys):
# 	"""Creates ONE draft Journal Entry for the selected transactions."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	keys = json.loads(keys) if isinstance(keys, str) else keys
# 	if not keys:
# 		frappe.throw(_("Please select at least one transaction."))

# 	from_date, to_date = getdate(from_date), getdate(to_date)
# 	rows = {r["key"]: r for r in _all_vat_rows(company, from_date, to_date)}

# 	selected = []
# 	for k in keys:
# 		if k not in rows:
# 			frappe.throw(_("{0} is no longer available for this return. Please reload and select again.").format(k))
# 		selected.append(rows[k])

# 	_check_filed_field()
# 	filed = _filed_vouchers(selected)
# 	already = sorted({r["doc_name"] for r in selected if (r["doc_type"], r["doc_name"]) in filed})
# 	if already:
# 		frappe.throw(_("Already included in another return: {0}").format(", ".join(already)))

# 	totals = {}
# 	for r in selected:
# 		totals[r["bucket"]] = totals.get(r["bucket"], 0) + r["vat"]

# 	accounts = _vat_accounts(company)
# 	lines, net = _build_vat_lines(totals, accounts)
# 	if not lines:
# 		frappe.throw(_("The selected transactions have no VAT amount to post."))
# 	_check_accounts([l["account"] for l in lines])

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Journal Entry"
# 	je.company = company
# 	je.posting_date = to_date
# 	je.user_remark = "{0} {1} | {2} to {3}\nVouchers: {4}".format(
# 		VAT_JE_MARKER,
# 		company,
# 		from_date,
# 		to_date,
# 		", ".join(sorted({r["doc_name"] for r in selected})),
# 	)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()  # stays in Draft so the accountant can review and submit

# 	if MARK_FILED_ON_JE:
# 		for dt, name in {(r["doc_type"], r["doc_name"]) for r in selected}:
# 			frappe.db.set_value(dt, name, VAT_FILED_FIELD, 1, update_modified=False)

# 	output = sum(flt(totals.get(k, 0)) for k in ("output_vat", "output_vat_rcm"))
# 	inp = sum(flt(totals.get(k, 0)) for k in ("input_vat", "input_vat_rcm"))
# 	return {
# 		"name": je.name,
# 		"output": flt(output, 2),
# 		"input": flt(inp, 2),
# 		"net": net,  # > 0 payable, < 0 refundable (VAT Payable goes negative)
# 	}


# @frappe.whitelist()
# def create_vat_settlement_entry(journal_entry, bank_account, posting_date, reference_no, reference_date):
# 	"""Payment of VAT Payable (Dr VAT Payable, Cr Bank) or, when the VAT Payable balance of the
# 	return is negative, receipt of the refund (Dr Bank, Cr VAT Payable) as a draft Bank Entry."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	src = frappe.get_doc("Journal Entry", journal_entry)
# 	if not (src.user_remark or "").startswith(VAT_JE_MARKER) or src.docstatus == 2:
# 		frappe.throw(_("{0} is not a valid VAT Journal Entry.").format(journal_entry))

# 	marker = "{0} {1}".format(VAT_SETTLE_MARKER, src.name)
# 	if frappe.db.exists(
# 		"Journal Entry", {"docstatus": ["<", 2], "user_remark": ["like", marker + "%"]}
# 	):
# 		frappe.throw(_("A payment/refund entry already exists for {0}.").format(src.name))

# 	accounts = _vat_accounts(src.company)
# 	if frappe.db.get_value("Account", bank_account, "company") != src.company:
# 		frappe.throw(_("{0} does not belong to {1}.").format(bank_account, src.company))

# 	# credit - debit on VAT Payable: > 0 = amount to pay, < 0 = refund to receive
# 	payable = sum(
# 		flt(r.credit_in_account_currency) - flt(r.debit_in_account_currency)
# 		for r in src.accounts
# 		if r.account == accounts["vat_payable"]
# 	)

# 	if payable > 0:
# 		amount = flt(payable, 2)
# 		lines = [
# 			{"account": accounts["vat_payable"], "debit_in_account_currency": amount},
# 			{"account": bank_account, "credit_in_account_currency": amount},
# 		]
# 	elif payable < 0:
# 		amount = flt(-payable, 2)
# 		lines = [
# 			{"account": bank_account, "debit_in_account_currency": amount},
# 			{"account": accounts["vat_payable"], "credit_in_account_currency": amount},
# 		]
# 	else:
# 		frappe.throw(_("There is no VAT payable or refundable to settle in {0}.").format(src.name))

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Bank Entry"
# 	je.company = src.company
# 	je.posting_date = getdate(posting_date)
# 	je.cheque_no = reference_no
# 	je.cheque_date = getdate(reference_date)
# 	je.user_remark = "{0}\nVAT payment/refund for {1}".format(marker, src.name)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()
# 	return je.name


# ###########################################################

# import json
# import re

# import frappe
# from frappe import _
# from frappe.utils import add_days, add_months, flt, getdate

# # Sales Invoices whose Sales Taxes and Charges Template has "Exclude from VAT Report" ticked
# # carry this flag (fetched from the template) and are left out of every figure in this report.
# EXCLUDE_SI_FIELD = "custom_exclude_from_vat_report"


# def execute(filters=None):
# 	filters = filters or {}
# 	if not filters.get("company"):  # first page load runs the report with empty filters
# 		return get_columns(), []
# 	if filters.get("drilldown_key") == "vat_transactions":
# 		return get_vat_transactions(filters)
# 	if filters.get("drilldown_key"):
# 		return get_drilldown(filters)
# 	columns = get_columns()
# 	data, emirates, amounts_by_emirate = get_data(filters)
# 	return columns, data


# # ------------------------------------------------------------------
# # Summary columns
# # ------------------------------------------------------------------


# def get_columns():
# 	return [
# 		{"fieldname": "no", "label": _("No"), "fieldtype": "Data", "width": 50},
# 		{"fieldname": "legend", "label": _("Legend"), "fieldtype": "Data", "width": 300},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 125},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# # ------------------------------------------------------------------
# # Summary data
# # ------------------------------------------------------------------


# def get_data(filters=None):
# 	data = []
# 	emirates, amounts_by_emirate = append_vat_on_sales(data, filters)
# 	append_vat_on_expenses(data, filters)
# 	return data, emirates, amounts_by_emirate


# def append_vat_on_sales(data, filters):
# 	append_data(data, "", _("VAT on Sales and All Other Outputs"), "", "")

# 	emirates, amounts_by_emirate = standard_rated_expenses_emiratewise(data, filters)

# 	total_amounts = [amounts_by_emirate.get(e, {}).get("raw_amount", 0) for e in emirates]
# 	total_vat_amounts = [amounts_by_emirate.get(e, {}).get("raw_vat_amount", 0) for e in emirates]

# 	tourist_total = get_tourist_tax_return_total(filters)
# 	tourist_tax = get_tourist_tax_return_tax(filters)
# 	append_data(
# 		data,
# 		"2",
# 		_("Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme"),
# 		frappe.format((-1) * tourist_total, "Currency"),
# 		frappe.format((-1) * tourist_tax, "Currency"),
# 		drilldown_key="tourist_refund",
# 		raw_amount=(-1) * tourist_total,
# 		raw_vat_amount=(-1) * tourist_tax,
# 	)
# 	total_amounts.append((-1) * tourist_total)
# 	total_vat_amounts.append((-1) * tourist_tax)

# 	rc_total = get_reverse_charge_total(filters)
# 	rc_tax = get_reverse_charge_tax(filters)
# 	append_data(
# 		data,
# 		"3",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_total, "Currency"),
# 		frappe.format(rc_tax, "Currency"),
# 		drilldown_key="reverse_charge_sales",
# 		raw_amount=rc_total,
# 		raw_vat_amount=rc_tax,
# 	)
# 	total_amounts.append(rc_total)
# 	total_vat_amounts.append(rc_tax)

# 	zero_total = get_zero_rated_total(filters)
# 	append_data(
# 		data,
# 		"4",
# 		_("Zero Rated"),
# 		frappe.format(zero_total, "Currency"),
# 		"-",
# 		drilldown_key="zero_rated",
# 		raw_amount=zero_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(zero_total)

# 	exempt_total = get_exempt_total(filters)
# 	append_data(
# 		data,
# 		"5",
# 		_("Exempt Supplies"),
# 		frappe.format(exempt_total, "Currency"),
# 		"-",
# 		drilldown_key="exempt",
# 		raw_amount=exempt_total,
# 		raw_vat_amount=0,
# 	)
# 	total_amounts.append(exempt_total)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Sales and All Other Outputs"),
# 		frappe.format(sum(total_amounts), "Currency"),
# 		frappe.format(sum(total_vat_amounts), "Currency"),
# 	)

# 	append_data(data, "", "", "", "")

# 	return emirates, amounts_by_emirate


# def standard_rated_expenses_emiratewise(data, filters):
# 	total_emiratewise = get_total_emiratewise(filters)
# 	emirates = get_emirates()
# 	amounts_by_emirate = {}
# 	for emirate, amount, vat in total_emiratewise:
# 		amounts_by_emirate[emirate] = {
# 			"legend": emirate,
# 			"raw_amount": flt(amount),
# 			"raw_vat_amount": flt(vat),
# 			"amount": frappe.format(amount, "Currency"),
# 			"vat_amount": frappe.format(vat, "Currency"),
# 		}
# 	amounts_by_emirate = append_emiratewise_expenses(data, emirates, amounts_by_emirate)
# 	return emirates, amounts_by_emirate


# def append_emiratewise_expenses(data, emirates, amounts_by_emirate):
# 	for no, emirate in enumerate(emirates, 97):
# 		key = "standard_rated_{0}".format(emirate)
# 		if emirate in amounts_by_emirate:
# 			amounts_by_emirate[emirate]["no"] = _("1{0}").format(chr(no))
# 			amounts_by_emirate[emirate]["legend"] = _("Standard rated supplies in {0}").format(emirate)
# 			amounts_by_emirate[emirate]["drilldown_key"] = key
# 			data.append(amounts_by_emirate[emirate])
# 		else:
# 			append_data(
# 				data,
# 				_("1{0}").format(chr(no)),
# 				_("Standard rated supplies in {0}").format(emirate),
# 				frappe.format(0, "Currency"),
# 				frappe.format(0, "Currency"),
# 				drilldown_key=key,
# 				raw_amount=0,
# 				raw_vat_amount=0,
# 			)
# 	return amounts_by_emirate


# def append_vat_on_expenses(data, filters):
# 	append_data(data, "", _("VAT on Expenses and All Other Inputs"), "", "")

# 	std_exp_total = get_standard_rated_expenses_total(filters)
# 	std_exp_tax = get_standard_rated_expenses_tax(filters)
# 	append_data(
# 		data,
# 		"9",
# 		_("Standard Rated Expenses"),
# 		frappe.format(std_exp_total, "Currency"),
# 		frappe.format(std_exp_tax, "Currency"),
# 		drilldown_key="standard_rated_expenses",
# 		raw_amount=std_exp_total,
# 		raw_vat_amount=std_exp_tax,
# 	)

# 	rc_rec_total = get_reverse_charge_recoverable_total(filters)
# 	rc_rec_tax = get_reverse_charge_recoverable_tax(filters)
# 	append_data(
# 		data,
# 		"10",
# 		_("Supplies subject to the reverse charge provision"),
# 		frappe.format(rc_rec_total, "Currency"),
# 		frappe.format(rc_rec_tax, "Currency"),
# 		drilldown_key="reverse_charge_expenses",
# 		raw_amount=rc_rec_total,
# 		raw_vat_amount=rc_rec_tax,
# 	)

# 	append_data(
# 		data,
# 		"",
# 		_("Total VAT on Expenses and All Other Inputs"),
# 		frappe.format(std_exp_total + rc_rec_total, "Currency"),
# 		frappe.format(std_exp_tax + rc_rec_tax, "Currency"),
# 	)


# def append_data(data, no, legend, amount, vat_amount, drilldown_key=None, raw_amount=0, raw_vat_amount=0):
# 	row = {"no": no, "legend": legend, "amount": amount, "vat_amount": vat_amount}
# 	if drilldown_key:
# 		row["drilldown_key"] = drilldown_key
# 		row["raw_amount"] = raw_amount
# 		row["raw_vat_amount"] = raw_vat_amount
# 	data.append(row)


# # ==================================================================
# # Drill-down
# # ==================================================================


# def get_drilldown(filters):
# 	key = filters.get("drilldown_key")
# 	company = filters.get("company")
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")

# 	purchase_keys = ("standard_rated_expenses", "reverse_charge_expenses", "expenses_total")
# 	if key in purchase_keys:
# 		columns, data = _get_purchase_detail(key, company, from_date, to_date)
# 	elif key == "reverse_charge_sales":
# 		columns = _purchase_detail_columns()
# 		data = _rc_sales_detail(company, from_date, to_date)
# 	else:
# 		columns, data = _get_sales_detail(key, company, from_date, to_date)

# 	return columns, data, None, None, None, True


# def _get_sales_detail(key, company, from_date, to_date):
# 	if key.startswith("standard_rated_"):
# 		emirate = key[len("standard_rated_") :]
# 		return _sales_invoice_breakdown(company, from_date, to_date, emirate=emirate)
# 	elif key == "tourist_refund":
# 		return _sales_invoice_breakdown(company, from_date, to_date, tourist_only=True)
# 	elif key == "zero_rated":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_zero_rated=True)
# 	elif key == "exempt":
# 		return _sales_invoice_breakdown(company, from_date, to_date, is_exempt=True)
# 	elif key == "sales_total":
# 		return _sales_invoice_breakdown(company, from_date, to_date)
# 	return [], []


# def _get_purchase_detail(key, company, from_date, to_date):
# 	columns = _purchase_detail_columns()
# 	if key == "standard_rated_expenses":
# 		data = _std_expenses_detail(company, from_date, to_date)
# 	elif key == "reverse_charge_expenses":
# 		data = _rc_expenses_detail(company, from_date, to_date)
# 	elif key == "expenses_total":
# 		data = _all_expenses_detail(company, from_date, to_date)
# 	else:
# 		data = []
# 	return columns, data


# def _purchase_detail_columns():
# 	return [
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{
# 			"fieldname": "doc_name",
# 			"label": _("Document No"),
# 			"fieldtype": "Dynamic Link",
# 			"options": "doc_type",
# 			"width": 180,
# 		},
# 		{"fieldname": "party", "label": _("Party"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "item", "label": _("Item"), "fieldtype": "Data", "width": 200},
# 		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 130},
# 		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
# 	]


# def _account_fieldname(account):
# 	"""Sanitize an account name for use as a column fieldname."""
# 	return "acc_" + re.sub(r"[^a-zA-Z0-9_]", "_", account)


# def _sales_invoice_breakdown(
# 	company, from_date, to_date, emirate=None, is_zero_rated=False, is_exempt=False, tourist_only=False
# ):
# 	"""Account-wise breakdown of qualifying Sales Invoices."""
# 	si_cond, si_params = _si_conditions(company, from_date, to_date)

# 	if tourist_only:
# 		invoices = frappe.db.sql_list(
# 			"SELECT si.name FROM `tabSales Invoice` si WHERE 1=1 "
# 			+ si_cond + " AND si.tourist_tax_return > 0",
# 			tuple(si_params),
# 		)
# 	else:
# 		item_cond = ""
# 		item_params = []
# 		if emirate:
# 			item_cond += " AND si.vat_emirate = %s"
# 			item_params.append(emirate)
# 		if is_zero_rated:
# 			item_cond += " AND sii.is_zero_rated = 1"
# 		elif is_exempt:
# 			item_cond += " AND sii.is_exempt = 1"
# 		else:
# 			item_cond += " AND sii.is_exempt != 1 AND sii.is_zero_rated != 1"

# 		invoices = frappe.db.sql_list(
# 			"SELECT DISTINCT si.name FROM `tabSales Invoice Item` sii "
# 			"INNER JOIN `tabSales Invoice` si ON si.name = sii.parent "
# 			"WHERE 1=1 " + si_cond + item_cond,
# 			tuple(si_params + item_params),
# 		)

# 	if not invoices:
# 		return _sales_breakdown_columns([], []), []

# 	invoices_tuple = tuple(invoices)

# 	headers = frappe.db.sql(
# 		"""
# 		SELECT si.name AS sales_invoice, si.posting_date, si.customer_name AS customer,
# 		       si.debit_to AS receivable_account, si.vat_emirate
# 		FROM `tabSales Invoice` si
# 		WHERE si.docstatus = 1 AND si.name IN %s
# 		ORDER BY si.posting_date
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	items = frappe.db.sql(
# 		"""
# 		SELECT sii.parent AS sales_invoice, sii.income_account, sii.base_net_amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# 		WHERE si.docstatus = 1 AND sii.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	taxes = frappe.db.sql(
# 		"""
# 		SELECT stc.parent AS sales_invoice, stc.account_head, stc.base_tax_amount
# 		FROM `tabSales Taxes and Charges` stc
# 		INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
# 		WHERE si.docstatus = 1 AND stc.parent IN %s
# 		""",
# 		(invoices_tuple,),
# 		as_dict=True,
# 	)

# 	income_accounts = sorted({r.income_account for r in items if r.income_account})
# 	tax_accounts = sorted({r.account_head for r in taxes if r.account_head})

# 	item_map = {}
# 	for r in items:
# 		item_map.setdefault(r.sales_invoice, []).append(r)

# 	tax_map = {}
# 	for r in taxes:
# 		tax_map.setdefault(r.sales_invoice, []).append(r)

# 	data = []
# 	for h in headers:
# 		row = {
# 			"voucher_type": "Sales Invoice",
# 			"sales_invoice": h.sales_invoice,
# 			"posting_date": h.posting_date,
# 			"customer": h.customer,
# 			"receivable_account": h.receivable_account,
# 			"vat_emirate": h.vat_emirate,
# 		}
# 		for acc in income_accounts:
# 			row[_account_fieldname(acc)] = 0
# 		for acc in tax_accounts:
# 			row[_account_fieldname(acc)] = 0

# 		net_total = 0
# 		for it in item_map.get(h.sales_invoice, []):
# 			net_total += flt(it.base_net_amount)
# 			if it.income_account:
# 				row[_account_fieldname(it.income_account)] = flt(row[_account_fieldname(it.income_account)]) + flt(
# 					it.base_net_amount
# 				)

# 		tax_total = 0
# 		for t in tax_map.get(h.sales_invoice, []):
# 			tax_total += flt(t.base_tax_amount)
# 			if t.account_head:
# 				row[_account_fieldname(t.account_head)] = flt(row[_account_fieldname(t.account_head)]) + flt(
# 					t.base_tax_amount
# 				)

# 		row["net_total"] = flt(net_total)
# 		row["tax_total"] = flt(tax_total)
# 		row["grand_total"] = flt(net_total + tax_total)
# 		data.append(row)

# 	columns = _sales_breakdown_columns(income_accounts, tax_accounts)
# 	return columns, data


# def _sales_breakdown_columns(income_accounts, tax_accounts):
# 	columns = [
# 		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 110},
# 		{
# 			"fieldname": "sales_invoice",
# 			"label": _("Sales Invoice No"),
# 			"fieldtype": "Link",
# 			"options": "Sales Invoice",
# 			"width": 150,
# 		},
# 		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
# 		{"fieldname": "vat_emirate", "label": _("VAT Emirates"), "fieldtype": "Data", "width": 140},
# 		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 220},
# 		{"fieldname": "receivable_account", "label": _("Receivable Account"), "fieldtype": "Data", "width": 220},
# 	]
# 	for acc in income_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	for acc in tax_accounts:
# 		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
# 	columns.extend(
# 		[
# 			{"fieldname": "net_total", "label": _("Net Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "tax_total", "label": _("Tax Total"), "fieldtype": "Currency", "width": 140},
# 			{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 150},
# 		]
# 	)
# 	return columns


# # ------------------------------------------------------------------
# # Condition builders
# # ------------------------------------------------------------------


# def _si_conditions(company, from_date, to_date):
# 	# CHANGED: invoices flagged "Exclude from VAT Report" are left out
# 	cond = "AND si.docstatus = 1 AND IFNULL(si.{0}, 0) = 0".format(EXCLUDE_SI_FIELD)
# 	params = []
# 	if company:
# 		cond += " AND si.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND si.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND si.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _pi_conditions(company, from_date, to_date):
# 	cond = "AND pi.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND pi.company = %s"
# 		params.append(company)
# 	if from_date:
# 		cond += " AND pi.posting_date >= %s"
# 		params.append(from_date)
# 	if to_date:
# 		cond += " AND pi.posting_date <= %s"
# 		params.append(to_date)
# 	return cond, params


# def _gl_conditions(company):
# 	cond = "AND gl.docstatus = 1"
# 	params = []
# 	if company:
# 		cond += " AND gl.account IN (SELECT account FROM `tabUAE VAT Account` WHERE parent = %s)"
# 		params.append(company)
# 	return cond, params


# # ------------------------------------------------------------------
# # Sales-side detail queries
# # ------------------------------------------------------------------


# def _rc_sales_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, SUM(gl.debit) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Purchase-side detail queries
# # ------------------------------------------------------------------


# def _std_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	cond += " AND pi.recoverable_standard_rated_expenses > 0"

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		WHERE 1=1 {cond}
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# def _rc_expenses_detail(company, from_date, to_date):
# 	cond, params = _pi_conditions(company, from_date, to_date)
# 	gl_cond, gl_params = _gl_conditions(company)
# 	cond += " AND pi.reverse_charge = 'Y' AND pi.recoverable_reverse_charge > 0 " + gl_cond
# 	params.extend(gl_params)

# 	return frappe.db.sql(
# 		f"""
# 		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
# 		       pi.supplier_name AS party, '' AS item,
# 		       pi.base_total AS amount,
# 		       SUM(gl.debit * pi.recoverable_reverse_charge / 100) AS vat_amount
# 		FROM `tabPurchase Invoice` pi
# 		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
# 		WHERE 1=1 {cond}
# 		GROUP BY pi.name
# 		ORDER BY pi.posting_date
# 	""",
# 		tuple(params),
# 		as_dict=True,
# 	)


# # ------------------------------------------------------------------
# # Combined detail queries
# # ------------------------------------------------------------------


# def _all_expenses_detail(company, from_date, to_date):
# 	data = []
# 	data.extend(_std_expenses_detail(company, from_date, to_date))
# 	data.extend(_rc_expenses_detail(company, from_date, to_date))
# 	return data


# # ==================================================================
# # Original helper functions
# # ==================================================================


# def get_total_emiratewise(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return frappe.db.sql(
# 			f"""
# 			select
# 				s.vat_emirate as emirate, sum(i.base_net_amount) as total, sum(i.tax_amount)
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and i.is_exempt != 1 and i.is_zero_rated != 1
# 				{conditions}
# 			group by
# 				s.vat_emirate;
# 			""",
# 			filters,
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_emirates():
# 	return ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]


# def get_filters(filters):
# 	query_filters = []
# 	if filters.get("company"):
# 		query_filters.append(["company", "=", filters["company"]])
# 	if filters.get("from_date"):
# 		query_filters.append(["posting_date", ">=", filters["from_date"]])
# 	if filters.get("to_date"):  # fixed: was checking from_date
# 		query_filters.append(["posting_date", "<=", filters["to_date"]])
# 	return query_filters


# def get_reverse_charge_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select sum(debit)  from
# 			`tabPurchase Invoice` p inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no =  p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_reverse_charge_recoverable_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["reverse_charge", "=", "Y"])
# 	query_filters.append(["recoverable_reverse_charge", ">", "0"])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_reverse_charge_recoverable_tax(filters):
# 	conditions = get_conditions_join(filters)
# 	return (
# 		frappe.db.sql(
# 			f"""
# 		select
# 			sum(debit * p.recoverable_reverse_charge / 100)
# 		from
# 			`tabPurchase Invoice` p  inner join `tabGL Entry` gl
# 		on
# 			gl.voucher_no = p.name
# 		where
# 			p.reverse_charge = "Y"
# 			and p.docstatus = 1
# 			and p.recoverable_reverse_charge > 0
# 			and gl.docstatus = 1
# 			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
# 			{conditions} ;
# 		""",
# 			filters,
# 		)[0][0]
# 		or 0
# 	)


# def get_conditions_join(filters):
# 	conditions = ""
# 	for opts in (
# 		("company", " and p.company=%(company)s"),
# 		("from_date", " and p.posting_date>=%(from_date)s"),
# 		("to_date", " and p.posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	return conditions


# def get_standard_rated_expenses_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_standard_rated_expenses_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Purchase Invoice",
# 				filters=query_filters,
# 				fields=["sum(recoverable_standard_rated_expenses)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_total(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	query_filters.append([EXCLUDE_SI_FIELD, "=", 0])  # CHANGED
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_tourist_tax_return_tax(filters):
# 	query_filters = get_filters(filters)
# 	query_filters.append(["tourist_tax_return", ">", 0])
# 	query_filters.append(["docstatus", "=", 1])
# 	query_filters.append([EXCLUDE_SI_FIELD, "=", 0])  # CHANGED
# 	try:
# 		return (
# 			frappe.db.get_all(
# 				"Sales Invoice",
# 				filters=query_filters,
# 				fields=["sum(tourist_tax_return)"],
# 				as_list=True,
# 				limit=1,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_zero_rated_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_zero_rated = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_exempt_total(filters):
# 	conditions = get_conditions(filters)
# 	try:
# 		return (
# 			frappe.db.sql(
# 				f"""
# 			select
# 				sum(i.base_net_amount) as total
# 			from
# 				`tabSales Invoice Item` i inner join `tabSales Invoice` s
# 			on
# 				i.parent = s.name
# 			where
# 				s.docstatus = 1 and  i.is_exempt = 1
# 				{conditions} ;
# 			""",
# 				filters,
# 			)[0][0]
# 			or 0
# 		)
# 	except (IndexError, TypeError):
# 		return 0


# def get_conditions(filters):
# 	"""Used by the Sales Invoice (alias s) queries: emiratewise, zero rated and exempt."""
# 	conditions = ""
# 	for opts in (
# 		("company", " and company=%(company)s"),
# 		("from_date", " and posting_date>=%(from_date)s"),
# 		("to_date", " and posting_date<=%(to_date)s"),
# 	):
# 		if filters.get(opts[0]):
# 			conditions += opts[1]
# 	# CHANGED: leave out invoices flagged "Exclude from VAT Report"
# 	conditions += " and ifnull(s.{0}, 0) = 0".format(EXCLUDE_SI_FIELD)
# 	return conditions


# # ==================================================================
# # "See Transactions" review screen + automatic VAT Journal Entry
# # ==================================================================

# # VAT accounts used for the VAT Journal Entry.
# # Every company has its own chart of accounts, so we only store the ACCOUNT NUMBER here
# # (same number in all companies). The real account is looked up for the company selected
# # in the report, e.g. 213000 -> "213000 - Output VAT - OBR" for Orion Bus Rental.
# VAT_ACCOUNT_NUMBERS = {
# 	"output_vat": "213000",
# 	"output_vat_rcm": "213500",
# 	"input_vat": "118000",
# 	"input_vat_rcm": "185000",
# 	"vat_payable": "218010",
# }

# VAT_ACCOUNT_LABELS = {
# 	"output_vat": "Output VAT",
# 	"output_vat_rcm": "Output VAT RCM",
# 	"input_vat": "Input VAT",
# 	"input_vat_rcm": "Input VAT RCM",
# 	"vat_payable": "VAT Payable",
# }


# def _vat_accounts(company):
# 	"""Returns {"output_vat": "<full account name of THIS company>", ...}."""
# 	accounts, missing = {}, []
# 	abbr = frappe.get_cached_value("Company", company, "abbr")
# 	for key, number in VAT_ACCOUNT_NUMBERS.items():
# 		name = frappe.db.get_value(
# 			"Account", {"company": company, "account_number": number, "is_group": 0}, "name"
# 		)
# 		if not name:  # fallback: "<number> - <label> - <abbr>"
# 			guess = "{0} - {1} - {2}".format(number, VAT_ACCOUNT_LABELS[key], abbr)
# 			if frappe.db.exists("Account", {"name": guess, "company": company, "is_group": 0}):
# 				name = guess
# 		if name:
# 			accounts[key] = name
# 		else:
# 			missing.append("{0} ({1})".format(number, VAT_ACCOUNT_LABELS[key]))
# 	if missing:
# 		frappe.throw(
# 			_("{0} does not have these VAT accounts: {1}. Create them (account number must match) and try again.").format(
# 				company, ", ".join(missing)
# 			)
# 		)
# 	return accounts


# # First line of the Journal Entry remark. Used to find which vouchers were already filed.
# VAT_JE_MARKER = "UAE VAT 201 |"
# VAT_SETTLE_MARKER = "UAE VAT 201 Settlement |"


# def _all_vat_rows(company, from_date, to_date):
# 	periods = (
# 		("current", from_date, to_date),
# 		("previous", add_months(from_date, -3), add_days(from_date, -1)),
# 	)
# 	rows = []
# 	for section, start, end in periods:
# 		for r in _collect_vat_transactions(company, start, end):
# 			r["section"] = section
# 			r["key"] = "{0}|{1}".format(r["category"], r["doc_name"])
# 			rows.append(r)
# 	return rows


# def get_vat_transactions(filters):
# 	"""Transactions for the VAT 201 screen.
# 	Section 'current'  : ALL transactions in the selected period (flagged ones are locked).
# 	Section 'previous' : transactions of the 3 months before the period that are NOT yet
# 	                     flagged custom_vat_filed (Sales and Purchase)."""
# 	company = filters.get("company")
# 	_check_filed_field()
# 	all_rows = _all_vat_rows(company, getdate(filters.get("from_date")), getdate(filters.get("to_date")))
# 	filed = _filed_vouchers(all_rows)

# 	rows = []
# 	for r in all_rows:
# 		r["locked"] = (r["doc_type"], r["doc_name"]) in filed
# 		if r["section"] == "previous":
# 			if r["locked"]:
# 				continue  # already filed in an earlier return -> do not show again
# 			r["note"] = _("Not previously reported")
# 		else:
# 			r["note"] = _("Already filed in a previous VAT return") if r["locked"] else ""
# 		rows.append(r)

# 	columns = [
# 		{"fieldname": "section", "label": _("Section"), "fieldtype": "Data", "width": 90},
# 		{"fieldname": "doc_name", "label": _("Document No"), "fieldtype": "Data", "width": 160},
# 		{"fieldname": "vat", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 140},
# 	]
# 	return columns, rows


# def _sales_report_rows(company, start, end, kind):
# 	"""Sales invoices exactly as the original report counts them (one row per invoice)."""
# 	if kind == "standard":
# 		item_cond = "i.is_exempt != 1 AND i.is_zero_rated != 1 AND s.vat_emirate IN %(emirates)s"
# 	elif kind == "zero":
# 		item_cond = "i.is_zero_rated = 1"
# 	else:
# 		item_cond = "i.is_exempt = 1"

# 	company_cond = " AND s.company = %(company)s" if company else ""
# 	# CHANGED: invoices flagged "Exclude from VAT Report" are left out
# 	return frappe.db.sql(
# 		f"""
# 		SELECT s.name AS doc_name, s.posting_date, s.customer_name AS party,
# 		       SUM(i.base_net_amount) AS amount, SUM(i.tax_amount) AS vat
# 		FROM `tabSales Invoice Item` i
# 		INNER JOIN `tabSales Invoice` s ON i.parent = s.name
# 		WHERE s.docstatus = 1 AND {item_cond}
# 		  AND IFNULL(s.{EXCLUDE_SI_FIELD}, 0) = 0
# 		  AND s.posting_date >= %(start)s AND s.posting_date <= %(end)s
# 		  {company_cond}
# 		GROUP BY s.name
# 		ORDER BY s.posting_date
# 		""",
# 		{"company": company, "start": start, "end": end, "emirates": tuple(get_emirates())},
# 		as_dict=True,
# 	)


# def _collect_vat_transactions(company, start, end):
# 	out = []

# 	def add(doc_type, doc_name, posting_date, party, vtype, category, bucket, amount, vat):
# 		out.append(
# 			{
# 				"doc_type": doc_type,
# 				"doc_name": doc_name,
# 				"posting_date": str(posting_date),
# 				"party": party or "",
# 				"type": vtype,  # Sales = output VAT, Purchase = input VAT
# 				"category": category,
# 				"bucket": bucket,  # which VAT account this belongs to
# 				"amount": flt(amount),
# 				"vat": flt(vat),
# 			}
# 		)

# 	# Sales invoices - same rules as the original report's rows 1a-1g, 4 and 5:
# 	#  * Standard rated: items not zero-rated/exempt, and the invoice has a VAT Emirate set
# 	#    (VAT = sum of the item tax_amount, exactly like the summary)
# 	#  * Zero rated / Exempt: items flagged zero-rated / exempt (no VAT)
# 	for category, kind in (
# 		(_("Standard rated"), "standard"),
# 		(_("Zero rated"), "zero"),
# 		(_("Exempt"), "exempt"),
# 	):
# 		for d in _sales_report_rows(company, start, end, kind):
# 			add("Sales Invoice", d.doc_name, d.posting_date, d.party,
# 				"Sales", category, "output_vat", d.amount, d.vat if kind == "standard" else 0)

# 	# Tourist refunds (negative output VAT)
# 	tourist_filters = [
# 		["docstatus", "=", 1],
# 		["posting_date", "between", [start, end]],
# 		["tourist_tax_return", ">", 0],
# 		[EXCLUDE_SI_FIELD, "=", 0],  # CHANGED
# 	]
# 	if company:
# 		tourist_filters.append(["company", "=", company])
# 	for d in frappe.get_all(
# 		"Sales Invoice",
# 		filters=tourist_filters,
# 		fields=["name", "posting_date", "customer_name", "base_total", "tourist_tax_return"],
# 	):
# 		add("Sales Invoice", d.name, d.posting_date, d.customer_name, "Sales",
# 			_("Tourist refund"), "output_vat", -flt(d.base_total), -flt(d.tourist_tax_return))

# 	# Reverse charge - output side
# 	for d in _rc_sales_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Sales",
# 			_("Reverse charge (output)"), "output_vat_rcm", d.amount, d.vat_amount)

# 	# Purchases - input side
# 	for d in _std_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Standard rated expense"), "input_vat", d.amount, d.vat_amount)

# 	for d in _rc_expenses_detail(company, start, end):
# 		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
# 			_("Reverse charge (input)"), "input_vat_rcm", d.amount, d.vat_amount)

# 	return sorted(out, key=lambda r: (r["posting_date"], r["doc_name"]))


# VAT_FILED_FIELD = "custom_vat_filed"  # Check field on Sales Invoice and Purchase Invoice
# MARK_FILED_ON_JE = True  # tick custom_vat_filed on the selected vouchers when the Journal Entry is created


# def _check_filed_field():
# 	missing = [
# 		dt for dt in ("Sales Invoice", "Purchase Invoice") if not frappe.get_meta(dt).has_field(VAT_FILED_FIELD)
# 	]
# 	if missing:
# 		frappe.throw(
# 			_("Please add a Check field named {0} to: {1}").format(VAT_FILED_FIELD, ", ".join(missing))
# 		)
# 	# NEW: the exclusion flag must exist on Sales Invoice, otherwise the report queries fail
# 	if not frappe.get_meta("Sales Invoice").has_field(EXCLUDE_SI_FIELD):
# 		frappe.throw(
# 			_("Please add a Check field named {0} to Sales Invoice (fetch from the Sales Taxes and Charges Template).").format(
# 				EXCLUDE_SI_FIELD
# 			)
# 		)


# def _filed_vouchers(rows):
# 	"""Set of (doctype, name) that already have custom_vat_filed ticked."""
# 	filed = set()
# 	for dt in ("Sales Invoice", "Purchase Invoice"):
# 		names = list({r["doc_name"] for r in rows if r["doc_type"] == dt})
# 		if names:
# 			for n in frappe.get_all(dt, filters={"name": ["in", names], VAT_FILED_FIELD: 1}, pluck="name"):
# 				filed.add((dt, n))
# 	return filed


# def _build_vat_lines(totals, accounts):
# 	"""Journal Entry lines in two blocks, exactly like the accountant's format:

# 	  Output VAT            Dr
# 	  Output VAT RCM        Dr
# 	      VAT Payable             Cr   (total of the output block)

# 	  Input VAT                   Cr
# 	  Input VAT RCM               Cr
# 	  VAT Payable           Dr         (total of the input block)

# 	The two VAT Payable lines net to the VAT payable for the period. There is no separate
# 	"VAT Receivable" account: if input VAT is more than output VAT, VAT Payable simply ends
# 	with a debit (negative) balance, i.e. a refund is due."""
# 	lines = []

# 	def add(key, dr=0.0, cr=0.0):
# 		line = {"account": accounts[key]}
# 		if dr:
# 			line["debit_in_account_currency"] = dr
# 		if cr:
# 			line["credit_in_account_currency"] = cr
# 		lines.append(line)

# 	# ---- Block 1: output VAT (credit balance accounts -> debit to clear)
# 	out_net = 0.0  # debits minus credits of the block
# 	for key in ("output_vat", "output_vat_rcm"):
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			add(key, dr=amt)
# 		elif amt < 0:
# 			add(key, cr=-amt)
# 		out_net += amt
# 	out_net = flt(out_net, 2)

# 	# ---- Block 2: input VAT (debit balance accounts -> credit to clear)
# 	in_net = 0.0  # credits minus debits of the block
# 	for key in ("input_vat", "input_vat_rcm"):
# 		amt = flt(totals.get(key, 0), 2)
# 		if amt > 0:
# 			add(key, cr=amt)
# 		elif amt < 0:
# 			add(key, dr=-amt)
# 		in_net += amt
# 	in_net = flt(in_net, 2)

# 	net = flt(out_net - in_net, 2)  # > 0 payable, < 0 refundable (negative VAT Payable)

# 	# VAT Payable line of the output block goes right after the output lines
# 	# (credit when output > 0), then the input block lines, then its VAT Payable line.
# 	out_lines = [l for l in lines if l["account"] in (accounts["output_vat"], accounts["output_vat_rcm"])]
# 	in_lines = [l for l in lines if l["account"] in (accounts["input_vat"], accounts["input_vat_rcm"])]
# 	lines = list(out_lines)
# 	if out_net > 0:
# 		add("vat_payable", cr=out_net)
# 	elif out_net < 0:
# 		add("vat_payable", dr=-out_net)
# 	lines.extend(in_lines)

# 	if in_net > 0:
# 		add("vat_payable", dr=in_net)
# 	elif in_net < 0:
# 		add("vat_payable", cr=-in_net)
# 	return lines, net


# def _check_accounts(accounts):
# 	missing = [a for a in accounts if not frappe.db.exists("Account", a)]
# 	if missing:
# 		frappe.throw(
# 			_("These accounts were not found: {0}. Create them "
# 			"or correct VAT_ACCOUNT_NUMBERS in the report's Python file.").format(
# 				", ".join(missing)
# 			)
# 		)


# @frappe.whitelist()
# def create_vat_journal_entry(company, from_date, to_date, keys):
# 	"""Creates ONE draft Journal Entry for the selected transactions."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	keys = json.loads(keys) if isinstance(keys, str) else keys
# 	if not keys:
# 		frappe.throw(_("Please select at least one transaction."))

# 	from_date, to_date = getdate(from_date), getdate(to_date)
# 	rows = {r["key"]: r for r in _all_vat_rows(company, from_date, to_date)}

# 	selected = []
# 	for k in keys:
# 		if k not in rows:
# 			frappe.throw(_("{0} is no longer available for this return. Please reload and select again.").format(k))
# 		selected.append(rows[k])

# 	_check_filed_field()
# 	filed = _filed_vouchers(selected)
# 	already = sorted({r["doc_name"] for r in selected if (r["doc_type"], r["doc_name"]) in filed})
# 	if already:
# 		frappe.throw(_("Already included in another return: {0}").format(", ".join(already)))

# 	totals = {}
# 	for r in selected:
# 		totals[r["bucket"]] = totals.get(r["bucket"], 0) + r["vat"]

# 	accounts = _vat_accounts(company)
# 	lines, net = _build_vat_lines(totals, accounts)
# 	if not lines:
# 		frappe.throw(_("The selected transactions have no VAT amount to post."))
# 	_check_accounts([l["account"] for l in lines])

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Journal Entry"
# 	je.company = company
# 	je.posting_date = to_date
# 	je.user_remark = "{0} {1} | {2} to {3}\nVouchers: {4}".format(
# 		VAT_JE_MARKER,
# 		company,
# 		from_date,
# 		to_date,
# 		", ".join(sorted({r["doc_name"] for r in selected})),
# 	)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()  # stays in Draft so the accountant can review and submit

# 	if MARK_FILED_ON_JE:
# 		for dt, name in {(r["doc_type"], r["doc_name"]) for r in selected}:
# 			frappe.db.set_value(dt, name, VAT_FILED_FIELD, 1, update_modified=False)

# 	output = sum(flt(totals.get(k, 0)) for k in ("output_vat", "output_vat_rcm"))
# 	inp = sum(flt(totals.get(k, 0)) for k in ("input_vat", "input_vat_rcm"))
# 	return {
# 		"name": je.name,
# 		"output": flt(output, 2),
# 		"input": flt(inp, 2),
# 		"net": net,  # > 0 payable, < 0 refundable (VAT Payable goes negative)
# 	}


# @frappe.whitelist()
# def create_vat_settlement_entry(journal_entry, bank_account, posting_date, reference_no, reference_date):
# 	"""Payment of VAT Payable (Dr VAT Payable, Cr Bank) or, when the VAT Payable balance of the
# 	return is negative, receipt of the refund (Dr Bank, Cr VAT Payable) as a draft Bank Entry."""
# 	frappe.has_permission("Journal Entry", "create", throw=True)
# 	src = frappe.get_doc("Journal Entry", journal_entry)
# 	if not (src.user_remark or "").startswith(VAT_JE_MARKER) or src.docstatus == 2:
# 		frappe.throw(_("{0} is not a valid VAT Journal Entry.").format(journal_entry))

# 	marker = "{0} {1}".format(VAT_SETTLE_MARKER, src.name)
# 	if frappe.db.exists(
# 		"Journal Entry", {"docstatus": ["<", 2], "user_remark": ["like", marker + "%"]}
# 	):
# 		frappe.throw(_("A payment/refund entry already exists for {0}.").format(src.name))

# 	accounts = _vat_accounts(src.company)
# 	if frappe.db.get_value("Account", bank_account, "company") != src.company:
# 		frappe.throw(_("{0} does not belong to {1}.").format(bank_account, src.company))

# 	# credit - debit on VAT Payable: > 0 = amount to pay, < 0 = refund to receive
# 	payable = sum(
# 		flt(r.credit_in_account_currency) - flt(r.debit_in_account_currency)
# 		for r in src.accounts
# 		if r.account == accounts["vat_payable"]
# 	)

# 	if payable > 0:
# 		amount = flt(payable, 2)
# 		lines = [
# 			{"account": accounts["vat_payable"], "debit_in_account_currency": amount},
# 			{"account": bank_account, "credit_in_account_currency": amount},
# 		]
# 	elif payable < 0:
# 		amount = flt(-payable, 2)
# 		lines = [
# 			{"account": bank_account, "debit_in_account_currency": amount},
# 			{"account": accounts["vat_payable"], "credit_in_account_currency": amount},
# 		]
# 	else:
# 		frappe.throw(_("There is no VAT payable or refundable to settle in {0}.").format(src.name))

# 	je = frappe.new_doc("Journal Entry")
# 	je.voucher_type = "Bank Entry"
# 	je.company = src.company
# 	je.posting_date = getdate(posting_date)
# 	je.cheque_no = reference_no
# 	je.cheque_date = getdate(reference_date)
# 	je.user_remark = "{0}\nVAT payment/refund for {1}".format(marker, src.name)
# 	for l in lines:
# 		je.append("accounts", l)
# 	je.insert()
# 	return je.name




import json
import re

import frappe
from frappe import _
from frappe.utils import add_days, add_months, flt, getdate

# Sales Invoices whose Sales Taxes and Charges Template has "Exclude from VAT Report" ticked
# carry this flag (fetched from the template) and are left out of every figure in this report.
EXCLUDE_SI_FIELD = "custom_exclude_from_vat_report"

# Check field on Purchase Invoice Item. Items ticked with it are left out of the AMOUNT column
# (the VAT amount is not changed by this flag).
EXCLUDE_PI_ITEM_FIELD = "custom_exclude_from_vat_report"

# Amount of a Purchase Invoice (alias pi) without the items ticked "Exclude from VAT Report"
PI_AMOUNT_SQL = (
	"(SELECT IFNULL(SUM(pii.base_amount), 0) FROM `tabPurchase Invoice Item` pii "
	"WHERE pii.parent = pi.name AND IFNULL(pii.{0}, 0) = 0)"
).format(EXCLUDE_PI_ITEM_FIELD)


def execute(filters=None):
	filters = filters or {}
	if not filters.get("company"):  # first page load runs the report with empty filters
		return get_columns(), []
	if filters.get("drilldown_key") == "vat_transactions":
		return get_vat_transactions(filters)
	if filters.get("drilldown_key"):
		return get_drilldown(filters)
	columns = get_columns()
	data, emirates, amounts_by_emirate = get_data(filters)
	return columns, data


# ------------------------------------------------------------------
# Summary columns
# ------------------------------------------------------------------


def get_columns():
	return [
		{"fieldname": "no", "label": _("No"), "fieldtype": "Data", "width": 50},
		{"fieldname": "legend", "label": _("Legend"), "fieldtype": "Data", "width": 300},
		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 125},
		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
	]


# ------------------------------------------------------------------
# Summary data
# ------------------------------------------------------------------


def get_data(filters=None):
	data = []
	emirates, amounts_by_emirate = append_vat_on_sales(data, filters)
	append_vat_on_expenses(data, filters)
	return data, emirates, amounts_by_emirate


def append_vat_on_sales(data, filters):
	append_data(data, "", _("VAT on Sales and All Other Outputs"), "", "")

	emirates, amounts_by_emirate = standard_rated_expenses_emiratewise(data, filters)

	total_amounts = [amounts_by_emirate.get(e, {}).get("raw_amount", 0) for e in emirates]
	total_vat_amounts = [amounts_by_emirate.get(e, {}).get("raw_vat_amount", 0) for e in emirates]

	tourist_total = get_tourist_tax_return_total(filters)
	tourist_tax = get_tourist_tax_return_tax(filters)
	append_data(
		data,
		"2",
		_("Tax Refunds provided to Tourists under the Tax Refunds for Tourists Scheme"),
		frappe.format((-1) * tourist_total, "Currency"),
		frappe.format((-1) * tourist_tax, "Currency"),
		drilldown_key="tourist_refund",
		raw_amount=(-1) * tourist_total,
		raw_vat_amount=(-1) * tourist_tax,
	)
	total_amounts.append((-1) * tourist_total)
	total_vat_amounts.append((-1) * tourist_tax)

	rc_total = get_reverse_charge_total(filters)
	rc_tax = get_reverse_charge_tax(filters)
	append_data(
		data,
		"3",
		_("Supplies subject to the reverse charge provision"),
		frappe.format(rc_total, "Currency"),
		frappe.format(rc_tax, "Currency"),
		drilldown_key="reverse_charge_sales",
		raw_amount=rc_total,
		raw_vat_amount=rc_tax,
	)
	total_amounts.append(rc_total)
	total_vat_amounts.append(rc_tax)

	zero_total = get_zero_rated_total(filters)
	append_data(
		data,
		"4",
		_("Zero Rated"),
		frappe.format(zero_total, "Currency"),
		"-",
		drilldown_key="zero_rated",
		raw_amount=zero_total,
		raw_vat_amount=0,
	)
	total_amounts.append(zero_total)

	exempt_total = get_exempt_total(filters)
	append_data(
		data,
		"5",
		_("Exempt Supplies"),
		frappe.format(exempt_total, "Currency"),
		"-",
		drilldown_key="exempt",
		raw_amount=exempt_total,
		raw_vat_amount=0,
	)
	total_amounts.append(exempt_total)

	append_data(
		data,
		"",
		_("Total VAT on Sales and All Other Outputs"),
		frappe.format(sum(total_amounts), "Currency"),
		frappe.format(sum(total_vat_amounts), "Currency"),
	)

	append_data(data, "", "", "", "")

	return emirates, amounts_by_emirate


def standard_rated_expenses_emiratewise(data, filters):
	total_emiratewise = get_total_emiratewise(filters)
	emirates = get_emirates()
	amounts_by_emirate = {}
	for emirate, amount, vat in total_emiratewise:
		amounts_by_emirate[emirate] = {
			"legend": emirate,
			"raw_amount": flt(amount),
			"raw_vat_amount": flt(vat),
			"amount": frappe.format(amount, "Currency"),
			"vat_amount": frappe.format(vat, "Currency"),
		}
	amounts_by_emirate = append_emiratewise_expenses(data, emirates, amounts_by_emirate)
	return emirates, amounts_by_emirate


def append_emiratewise_expenses(data, emirates, amounts_by_emirate):
	for no, emirate in enumerate(emirates, 97):
		key = "standard_rated_{0}".format(emirate)
		if emirate in amounts_by_emirate:
			amounts_by_emirate[emirate]["no"] = _("1{0}").format(chr(no))
			amounts_by_emirate[emirate]["legend"] = _("Standard rated supplies in {0}").format(emirate)
			amounts_by_emirate[emirate]["drilldown_key"] = key
			data.append(amounts_by_emirate[emirate])
		else:
			append_data(
				data,
				_("1{0}").format(chr(no)),
				_("Standard rated supplies in {0}").format(emirate),
				frappe.format(0, "Currency"),
				frappe.format(0, "Currency"),
				drilldown_key=key,
				raw_amount=0,
				raw_vat_amount=0,
			)
	return amounts_by_emirate


def append_vat_on_expenses(data, filters):
	append_data(data, "", _("VAT on Expenses and All Other Inputs"), "", "")

	std_exp_total = get_standard_rated_expenses_total(filters)
	std_exp_tax = get_standard_rated_expenses_tax(filters)
	append_data(
		data,
		"9",
		_("Standard Rated Expenses"),
		frappe.format(std_exp_total, "Currency"),
		frappe.format(std_exp_tax, "Currency"),
		drilldown_key="standard_rated_expenses",
		raw_amount=std_exp_total,
		raw_vat_amount=std_exp_tax,
	)

	rc_rec_total = get_reverse_charge_recoverable_total(filters)
	rc_rec_tax = get_reverse_charge_recoverable_tax(filters)
	append_data(
		data,
		"10",
		_("Supplies subject to the reverse charge provision"),
		frappe.format(rc_rec_total, "Currency"),
		frappe.format(rc_rec_tax, "Currency"),
		drilldown_key="reverse_charge_expenses",
		raw_amount=rc_rec_total,
		raw_vat_amount=rc_rec_tax,
	)

	append_data(
		data,
		"",
		_("Total VAT on Expenses and All Other Inputs"),
		frappe.format(std_exp_total + rc_rec_total, "Currency"),
		frappe.format(std_exp_tax + rc_rec_tax, "Currency"),
	)


def append_data(data, no, legend, amount, vat_amount, drilldown_key=None, raw_amount=0, raw_vat_amount=0):
	row = {"no": no, "legend": legend, "amount": amount, "vat_amount": vat_amount}
	if drilldown_key:
		row["drilldown_key"] = drilldown_key
		row["raw_amount"] = raw_amount
		row["raw_vat_amount"] = raw_vat_amount
	data.append(row)


# ==================================================================
# Drill-down
# ==================================================================


def get_drilldown(filters):
	key = filters.get("drilldown_key")
	company = filters.get("company")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	purchase_keys = ("standard_rated_expenses", "reverse_charge_expenses", "expenses_total")
	if key in purchase_keys:
		columns, data = _get_purchase_detail(key, company, from_date, to_date)
	elif key == "reverse_charge_sales":
		columns = _purchase_detail_columns()
		data = _rc_sales_detail(company, from_date, to_date)
	else:
		columns, data = _get_sales_detail(key, company, from_date, to_date)

	return columns, data, None, None, None, True


def _get_sales_detail(key, company, from_date, to_date):
	if key.startswith("standard_rated_"):
		emirate = key[len("standard_rated_") :]
		return _sales_invoice_breakdown(company, from_date, to_date, emirate=emirate)
	elif key == "tourist_refund":
		return _sales_invoice_breakdown(company, from_date, to_date, tourist_only=True)
	elif key == "zero_rated":
		return _sales_invoice_breakdown(company, from_date, to_date, is_zero_rated=True)
	elif key == "exempt":
		return _sales_invoice_breakdown(company, from_date, to_date, is_exempt=True)
	elif key == "sales_total":
		return _sales_invoice_breakdown(company, from_date, to_date)
	return [], []


def _get_purchase_detail(key, company, from_date, to_date):
	columns = _purchase_detail_columns()
	if key == "standard_rated_expenses":
		data = _std_expenses_detail(company, from_date, to_date)
	elif key == "reverse_charge_expenses":
		data = _rc_expenses_detail(company, from_date, to_date)
	elif key == "expenses_total":
		data = _all_expenses_detail(company, from_date, to_date)
	else:
		data = []
	return columns, data


def _purchase_detail_columns():
	return [
		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
		{
			"fieldname": "doc_name",
			"label": _("Document No"),
			"fieldtype": "Dynamic Link",
			"options": "doc_type",
			"width": 180,
		},
		{"fieldname": "party", "label": _("Party"), "fieldtype": "Data", "width": 200},
		{"fieldname": "item", "label": _("Item"), "fieldtype": "Data", "width": 200},
		{"fieldname": "amount", "label": _("Amount (AED)"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "vat_amount", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 150},
	]


def _account_fieldname(account):
	"""Sanitize an account name for use as a column fieldname."""
	return "acc_" + re.sub(r"[^a-zA-Z0-9_]", "_", account)


def _sales_invoice_breakdown(
	company, from_date, to_date, emirate=None, is_zero_rated=False, is_exempt=False, tourist_only=False
):
	"""Account-wise breakdown of qualifying Sales Invoices."""
	si_cond, si_params = _si_conditions(company, from_date, to_date)

	if tourist_only:
		invoices = frappe.db.sql_list(
			"SELECT si.name FROM `tabSales Invoice` si WHERE 1=1 "
			+ si_cond + " AND si.tourist_tax_return > 0",
			tuple(si_params),
		)
	else:
		item_cond = ""
		item_params = []
		if emirate:
			item_cond += " AND si.vat_emirate = %s"
			item_params.append(emirate)
		if is_zero_rated:
			item_cond += " AND sii.is_zero_rated = 1"
		elif is_exempt:
			item_cond += " AND sii.is_exempt = 1"
		else:
			item_cond += " AND sii.is_exempt != 1 AND sii.is_zero_rated != 1"

		invoices = frappe.db.sql_list(
			"SELECT DISTINCT si.name FROM `tabSales Invoice Item` sii "
			"INNER JOIN `tabSales Invoice` si ON si.name = sii.parent "
			"WHERE 1=1 " + si_cond + item_cond,
			tuple(si_params + item_params),
		)

	if not invoices:
		return _sales_breakdown_columns([], []), []

	invoices_tuple = tuple(invoices)

	headers = frappe.db.sql(
		"""
		SELECT si.name AS sales_invoice, si.posting_date, si.customer_name AS customer,
		       si.debit_to AS receivable_account, si.vat_emirate
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1 AND si.name IN %s
		ORDER BY si.posting_date
		""",
		(invoices_tuple,),
		as_dict=True,
	)

	items = frappe.db.sql(
		"""
		SELECT sii.parent AS sales_invoice, sii.income_account, sii.base_net_amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 AND sii.parent IN %s
		""",
		(invoices_tuple,),
		as_dict=True,
	)

	taxes = frappe.db.sql(
		"""
		SELECT stc.parent AS sales_invoice, stc.account_head, stc.base_tax_amount
		FROM `tabSales Taxes and Charges` stc
		INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
		WHERE si.docstatus = 1 AND stc.parent IN %s
		""",
		(invoices_tuple,),
		as_dict=True,
	)

	income_accounts = sorted({r.income_account for r in items if r.income_account})
	tax_accounts = sorted({r.account_head for r in taxes if r.account_head})

	item_map = {}
	for r in items:
		item_map.setdefault(r.sales_invoice, []).append(r)

	tax_map = {}
	for r in taxes:
		tax_map.setdefault(r.sales_invoice, []).append(r)

	data = []
	for h in headers:
		row = {
			"voucher_type": "Sales Invoice",
			"sales_invoice": h.sales_invoice,
			"posting_date": h.posting_date,
			"customer": h.customer,
			"receivable_account": h.receivable_account,
			"vat_emirate": h.vat_emirate,
		}
		for acc in income_accounts:
			row[_account_fieldname(acc)] = 0
		for acc in tax_accounts:
			row[_account_fieldname(acc)] = 0

		net_total = 0
		for it in item_map.get(h.sales_invoice, []):
			net_total += flt(it.base_net_amount)
			if it.income_account:
				row[_account_fieldname(it.income_account)] = flt(row[_account_fieldname(it.income_account)]) + flt(
					it.base_net_amount
				)

		tax_total = 0
		for t in tax_map.get(h.sales_invoice, []):
			tax_total += flt(t.base_tax_amount)
			if t.account_head:
				row[_account_fieldname(t.account_head)] = flt(row[_account_fieldname(t.account_head)]) + flt(
					t.base_tax_amount
				)

		row["net_total"] = flt(net_total)
		row["tax_total"] = flt(tax_total)
		row["grand_total"] = flt(net_total + tax_total)
		data.append(row)

	columns = _sales_breakdown_columns(income_accounts, tax_accounts)
	return columns, data


def _sales_breakdown_columns(income_accounts, tax_accounts):
	columns = [
		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 110},
		{
			"fieldname": "sales_invoice",
			"label": _("Sales Invoice No"),
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 150,
		},
		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 110},
		{"fieldname": "vat_emirate", "label": _("VAT Emirates"), "fieldtype": "Data", "width": 140},
		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 220},
		{"fieldname": "receivable_account", "label": _("Receivable Account"), "fieldtype": "Data", "width": 220},
	]
	for acc in income_accounts:
		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
	for acc in tax_accounts:
		columns.append({"fieldname": _account_fieldname(acc), "label": acc, "fieldtype": "Currency", "width": 140})
	columns.extend(
		[
			{"fieldname": "net_total", "label": _("Net Total"), "fieldtype": "Currency", "width": 140},
			{"fieldname": "tax_total", "label": _("Tax Total"), "fieldtype": "Currency", "width": 140},
			{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 150},
		]
	)
	return columns


# ------------------------------------------------------------------
# Condition builders
# ------------------------------------------------------------------


def _si_conditions(company, from_date, to_date):
	# CHANGED: invoices flagged "Exclude from VAT Report" are left out
	cond = "AND si.docstatus = 1 AND IFNULL(si.{0}, 0) = 0".format(EXCLUDE_SI_FIELD)
	params = []
	if company:
		cond += " AND si.company = %s"
		params.append(company)
	if from_date:
		cond += " AND si.posting_date >= %s"
		params.append(from_date)
	if to_date:
		cond += " AND si.posting_date <= %s"
		params.append(to_date)
	return cond, params


def _pi_conditions(company, from_date, to_date):
	cond = "AND pi.docstatus = 1"
	params = []
	if company:
		cond += " AND pi.company = %s"
		params.append(company)
	if from_date:
		cond += " AND pi.posting_date >= %s"
		params.append(from_date)
	if to_date:
		cond += " AND pi.posting_date <= %s"
		params.append(to_date)
	return cond, params


def _gl_conditions(company):
	cond = "AND gl.docstatus = 1"
	params = []
	if company:
		cond += " AND gl.account IN (SELECT account FROM `tabUAE VAT Account` WHERE parent = %s)"
		params.append(company)
	return cond, params


# ------------------------------------------------------------------
# Sales-side detail queries
# ------------------------------------------------------------------


def _rc_sales_detail(company, from_date, to_date):
	cond, params = _pi_conditions(company, from_date, to_date)
	gl_cond, gl_params = _gl_conditions(company)
	cond += " AND pi.reverse_charge = 'Y' " + gl_cond
	params.extend(gl_params)

	# CHANGED: amount excludes items ticked "Exclude from VAT Report"
	return frappe.db.sql(
		f"""
		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
		       pi.supplier_name AS party, '' AS item,
		       {PI_AMOUNT_SQL} AS amount, SUM(gl.debit) AS vat_amount
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
		WHERE 1=1 {cond}
		GROUP BY pi.name
		ORDER BY pi.posting_date
	""",
		tuple(params),
		as_dict=True,
	)


# ------------------------------------------------------------------
# Purchase-side detail queries
# ------------------------------------------------------------------


def _std_expenses_detail(company, from_date, to_date):
	cond, params = _pi_conditions(company, from_date, to_date)
	cond += " AND pi.recoverable_standard_rated_expenses > 0"

	# CHANGED: amount excludes items ticked "Exclude from VAT Report"
	return frappe.db.sql(
		f"""
		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
		       pi.supplier_name AS party, '' AS item,
		       {PI_AMOUNT_SQL} AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
		FROM `tabPurchase Invoice` pi
		WHERE 1=1 {cond}
		ORDER BY pi.posting_date
	""",
		tuple(params),
		as_dict=True,
	)


def _rc_expenses_detail(company, from_date, to_date):
	cond, params = _pi_conditions(company, from_date, to_date)
	gl_cond, gl_params = _gl_conditions(company)
	cond += " AND pi.reverse_charge = 'Y' AND pi.recoverable_reverse_charge > 0 " + gl_cond
	params.extend(gl_params)

	# CHANGED: amount excludes items ticked "Exclude from VAT Report"
	return frappe.db.sql(
		f"""
		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
		       pi.supplier_name AS party, '' AS item,
		       {PI_AMOUNT_SQL} AS amount,
		       SUM(gl.debit * pi.recoverable_reverse_charge / 100) AS vat_amount
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabGL Entry` gl ON gl.voucher_no = pi.name
		WHERE 1=1 {cond}
		GROUP BY pi.name
		ORDER BY pi.posting_date
	""",
		tuple(params),
		as_dict=True,
	)


# ------------------------------------------------------------------
# Combined detail queries
# ------------------------------------------------------------------


def _all_expenses_detail(company, from_date, to_date):
	data = []
	data.extend(_std_expenses_detail(company, from_date, to_date))
	data.extend(_rc_expenses_detail(company, from_date, to_date))
	return data


# ==================================================================
# Original helper functions
# ==================================================================


def get_total_emiratewise(filters):
	conditions = get_conditions(filters)
	try:
		return frappe.db.sql(
			f"""
			select
				s.vat_emirate as emirate, sum(i.base_net_amount) as total, sum(i.tax_amount)
			from
				`tabSales Invoice Item` i inner join `tabSales Invoice` s
			on
				i.parent = s.name
			where
				s.docstatus = 1 and i.is_exempt != 1 and i.is_zero_rated != 1
				{conditions}
			group by
				s.vat_emirate;
			""",
			filters,
		)
	except (IndexError, TypeError):
		return 0


def get_emirates():
	return ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]


def get_filters(filters):
	query_filters = []
	if filters.get("company"):
		query_filters.append(["company", "=", filters["company"]])
	if filters.get("from_date"):
		query_filters.append(["posting_date", ">=", filters["from_date"]])
	if filters.get("to_date"):  # fixed: was checking from_date
		query_filters.append(["posting_date", "<=", filters["to_date"]])
	return query_filters


def _purchase_amount_total(filters, extra_cond=""):
	"""Sum of item amounts of submitted Purchase Invoices (alias p),
	skipping items ticked "Exclude from VAT Report"."""
	conditions = get_conditions_join(filters)
	return (
		frappe.db.sql(
			f"""
			SELECT SUM(pii.base_amount)
			FROM `tabPurchase Invoice Item` pii
			INNER JOIN `tabPurchase Invoice` p ON p.name = pii.parent
			WHERE p.docstatus = 1
			  AND IFNULL(pii.{EXCLUDE_PI_ITEM_FIELD}, 0) = 0
			  {extra_cond} {conditions}
			""",
			filters,
		)[0][0]
		or 0
	)


def get_reverse_charge_total(filters):  # row 3 (reverse charge, sales side)
	return _purchase_amount_total(filters, " AND p.reverse_charge = 'Y'")


def get_reverse_charge_tax(filters):
	conditions = get_conditions_join(filters)
	return (
		frappe.db.sql(
			f"""
		select sum(debit)  from
			`tabPurchase Invoice` p inner join `tabGL Entry` gl
		on
			gl.voucher_no =  p.name
		where
			p.reverse_charge = "Y"
			and p.docstatus = 1
			and gl.docstatus = 1
			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
			{conditions} ;
		""",
			filters,
		)[0][0]
		or 0
	)


def get_reverse_charge_recoverable_total(filters):  # row 10
	return _purchase_amount_total(
		filters, " AND p.reverse_charge = 'Y' AND p.recoverable_reverse_charge > 0"
	)


def get_reverse_charge_recoverable_tax(filters):
	conditions = get_conditions_join(filters)
	return (
		frappe.db.sql(
			f"""
		select
			sum(debit * p.recoverable_reverse_charge / 100)
		from
			`tabPurchase Invoice` p  inner join `tabGL Entry` gl
		on
			gl.voucher_no = p.name
		where
			p.reverse_charge = "Y"
			and p.docstatus = 1
			and p.recoverable_reverse_charge > 0
			and gl.docstatus = 1
			and account in (select account from `tabUAE VAT Account` where  parent=%(company)s)
			{conditions} ;
		""",
			filters,
		)[0][0]
		or 0
	)


def get_conditions_join(filters):
	conditions = ""
	for opts in (
		("company", " and p.company=%(company)s"),
		("from_date", " and p.posting_date>=%(from_date)s"),
		("to_date", " and p.posting_date<=%(to_date)s"),
	):
		if filters.get(opts[0]):
			conditions += opts[1]
	return conditions


def get_standard_rated_expenses_total(filters):  # row 9
	return _purchase_amount_total(filters, " AND p.recoverable_standard_rated_expenses > 0")


def get_standard_rated_expenses_tax(filters):
	query_filters = get_filters(filters)
	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
	query_filters.append(["docstatus", "=", 1])
	try:
		return (
			frappe.db.get_all(
				"Purchase Invoice",
				filters=query_filters,
				fields=["sum(recoverable_standard_rated_expenses)"],
				as_list=True,
				limit=1,
			)[0][0]
			or 0
		)
	except (IndexError, TypeError):
		return 0


def get_tourist_tax_return_total(filters):
	query_filters = get_filters(filters)
	query_filters.append(["tourist_tax_return", ">", 0])
	query_filters.append(["docstatus", "=", 1])
	query_filters.append([EXCLUDE_SI_FIELD, "=", 0])  # CHANGED
	try:
		return (
			frappe.db.get_all(
				"Sales Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
			)[0][0]
			or 0
		)
	except (IndexError, TypeError):
		return 0


def get_tourist_tax_return_tax(filters):
	query_filters = get_filters(filters)
	query_filters.append(["tourist_tax_return", ">", 0])
	query_filters.append(["docstatus", "=", 1])
	query_filters.append([EXCLUDE_SI_FIELD, "=", 0])  # CHANGED
	try:
		return (
			frappe.db.get_all(
				"Sales Invoice",
				filters=query_filters,
				fields=["sum(tourist_tax_return)"],
				as_list=True,
				limit=1,
			)[0][0]
			or 0
		)
	except (IndexError, TypeError):
		return 0


def get_zero_rated_total(filters):
	conditions = get_conditions(filters)
	try:
		return (
			frappe.db.sql(
				f"""
			select
				sum(i.base_net_amount) as total
			from
				`tabSales Invoice Item` i inner join `tabSales Invoice` s
			on
				i.parent = s.name
			where
				s.docstatus = 1 and  i.is_zero_rated = 1
				{conditions} ;
			""",
				filters,
			)[0][0]
			or 0
		)
	except (IndexError, TypeError):
		return 0


def get_exempt_total(filters):
	conditions = get_conditions(filters)
	try:
		return (
			frappe.db.sql(
				f"""
			select
				sum(i.base_net_amount) as total
			from
				`tabSales Invoice Item` i inner join `tabSales Invoice` s
			on
				i.parent = s.name
			where
				s.docstatus = 1 and  i.is_exempt = 1
				{conditions} ;
			""",
				filters,
			)[0][0]
			or 0
		)
	except (IndexError, TypeError):
		return 0


def get_conditions(filters):
	"""Used by the Sales Invoice (alias s) queries: emiratewise, zero rated and exempt."""
	conditions = ""
	for opts in (
		("company", " and company=%(company)s"),
		("from_date", " and posting_date>=%(from_date)s"),
		("to_date", " and posting_date<=%(to_date)s"),
	):
		if filters.get(opts[0]):
			conditions += opts[1]
	# CHANGED: leave out invoices flagged "Exclude from VAT Report"
	conditions += " and ifnull(s.{0}, 0) = 0".format(EXCLUDE_SI_FIELD)
	return conditions


# ==================================================================
# "See Transactions" review screen + automatic VAT Journal Entry
# ==================================================================

# VAT accounts used for the VAT Journal Entry.
# Every company has its own chart of accounts, so we only store the ACCOUNT NUMBER here
# (same number in all companies). The real account is looked up for the company selected
# in the report, e.g. 213000 -> "213000 - Output VAT - OBR" for Orion Bus Rental.
VAT_ACCOUNT_NUMBERS = {
	"output_vat": "213000",
	"output_vat_rcm": "213500",
	"input_vat": "118000",
	"input_vat_rcm": "185000",
	"vat_payable": "218010",
}

VAT_ACCOUNT_LABELS = {
	"output_vat": "Output VAT",
	"output_vat_rcm": "Output VAT RCM",
	"input_vat": "Input VAT",
	"input_vat_rcm": "Input VAT RCM",
	"vat_payable": "VAT Payable",
}


def _vat_accounts(company):
	"""Returns {"output_vat": "<full account name of THIS company>", ...}."""
	accounts, missing = {}, []
	abbr = frappe.get_cached_value("Company", company, "abbr")
	for key, number in VAT_ACCOUNT_NUMBERS.items():
		name = frappe.db.get_value(
			"Account", {"company": company, "account_number": number, "is_group": 0}, "name"
		)
		if not name:  # fallback: "<number> - <label> - <abbr>"
			guess = "{0} - {1} - {2}".format(number, VAT_ACCOUNT_LABELS[key], abbr)
			if frappe.db.exists("Account", {"name": guess, "company": company, "is_group": 0}):
				name = guess
		if name:
			accounts[key] = name
		else:
			missing.append("{0} ({1})".format(number, VAT_ACCOUNT_LABELS[key]))
	if missing:
		frappe.throw(
			_("{0} does not have these VAT accounts: {1}. Create them (account number must match) and try again.").format(
				company, ", ".join(missing)
			)
		)
	return accounts


# First line of the Journal Entry remark. Used to find which vouchers were already filed.
VAT_JE_MARKER = "UAE VAT 201 |"
VAT_SETTLE_MARKER = "UAE VAT 201 Settlement |"


def _all_vat_rows(company, from_date, to_date):
	periods = (
		("current", from_date, to_date),
		("previous", add_months(from_date, -3), add_days(from_date, -1)),
	)
	rows = []
	for section, start, end in periods:
		for r in _collect_vat_transactions(company, start, end):
			r["section"] = section
			r["key"] = "{0}|{1}".format(r["category"], r["doc_name"])
			rows.append(r)
	return rows


def get_vat_transactions(filters):
	"""Transactions for the VAT 201 screen.
	Section 'current'  : ALL transactions in the selected period (flagged ones are locked).
	Section 'previous' : transactions of the 3 months before the period that are NOT yet
	                     flagged custom_vat_filed (Sales and Purchase)."""
	company = filters.get("company")
	_check_filed_field()
	all_rows = _all_vat_rows(company, getdate(filters.get("from_date")), getdate(filters.get("to_date")))
	filed = _filed_vouchers(all_rows)

	rows = []
	for r in all_rows:
		r["locked"] = (r["doc_type"], r["doc_name"]) in filed
		if r["section"] == "previous":
			if r["locked"]:
				continue  # already filed in an earlier return -> do not show again
			r["note"] = _("Not previously reported")
		else:
			r["note"] = _("Already filed in a previous VAT return") if r["locked"] else ""
		rows.append(r)

	columns = [
		{"fieldname": "section", "label": _("Section"), "fieldtype": "Data", "width": 90},
		{"fieldname": "doc_name", "label": _("Document No"), "fieldtype": "Data", "width": 160},
		{"fieldname": "vat", "label": _("VAT Amount (AED)"), "fieldtype": "Currency", "width": 140},
	]
	return columns, rows


def _sales_report_rows(company, start, end, kind):
	"""Sales invoices exactly as the original report counts them (one row per invoice)."""
	if kind == "standard":
		item_cond = "i.is_exempt != 1 AND i.is_zero_rated != 1 AND s.vat_emirate IN %(emirates)s"
	elif kind == "zero":
		item_cond = "i.is_zero_rated = 1"
	else:
		item_cond = "i.is_exempt = 1"

	company_cond = " AND s.company = %(company)s" if company else ""
	# CHANGED: invoices flagged "Exclude from VAT Report" are left out
	return frappe.db.sql(
		f"""
		SELECT s.name AS doc_name, s.posting_date, s.customer_name AS party,
		       SUM(i.base_net_amount) AS amount, SUM(i.tax_amount) AS vat
		FROM `tabSales Invoice Item` i
		INNER JOIN `tabSales Invoice` s ON i.parent = s.name
		WHERE s.docstatus = 1 AND {item_cond}
		  AND IFNULL(s.{EXCLUDE_SI_FIELD}, 0) = 0
		  AND s.posting_date >= %(start)s AND s.posting_date <= %(end)s
		  {company_cond}
		GROUP BY s.name
		ORDER BY s.posting_date
		""",
		{"company": company, "start": start, "end": end, "emirates": tuple(get_emirates())},
		as_dict=True,
	)


def _collect_vat_transactions(company, start, end):
	out = []

	def add(doc_type, doc_name, posting_date, party, vtype, category, bucket, amount, vat):
		out.append(
			{
				"doc_type": doc_type,
				"doc_name": doc_name,
				"posting_date": str(posting_date),
				"party": party or "",
				"type": vtype,  # Sales = output VAT, Purchase = input VAT
				"category": category,
				"bucket": bucket,  # which VAT account this belongs to
				"amount": flt(amount),
				"vat": flt(vat),
			}
		)

	# Sales invoices - same rules as the original report's rows 1a-1g, 4 and 5:
	#  * Standard rated: items not zero-rated/exempt, and the invoice has a VAT Emirate set
	#    (VAT = sum of the item tax_amount, exactly like the summary)
	#  * Zero rated / Exempt: items flagged zero-rated / exempt (no VAT)
	for category, kind in (
		(_("Standard rated"), "standard"),
		(_("Zero rated"), "zero"),
		(_("Exempt"), "exempt"),
	):
		for d in _sales_report_rows(company, start, end, kind):
			add("Sales Invoice", d.doc_name, d.posting_date, d.party,
				"Sales", category, "output_vat", d.amount, d.vat if kind == "standard" else 0)

	# Tourist refunds (negative output VAT)
	tourist_filters = [
		["docstatus", "=", 1],
		["posting_date", "between", [start, end]],
		["tourist_tax_return", ">", 0],
		[EXCLUDE_SI_FIELD, "=", 0],  # CHANGED
	]
	if company:
		tourist_filters.append(["company", "=", company])
	for d in frappe.get_all(
		"Sales Invoice",
		filters=tourist_filters,
		fields=["name", "posting_date", "customer_name", "base_total", "tourist_tax_return"],
	):
		add("Sales Invoice", d.name, d.posting_date, d.customer_name, "Sales",
			_("Tourist refund"), "output_vat", -flt(d.base_total), -flt(d.tourist_tax_return))

	# Reverse charge - output side
	for d in _rc_sales_detail(company, start, end):
		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Sales",
			_("Reverse charge (output)"), "output_vat_rcm", d.amount, d.vat_amount)

	# Purchases - input side
	for d in _std_expenses_detail(company, start, end):
		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
			_("Standard rated expense"), "input_vat", d.amount, d.vat_amount)

	for d in _rc_expenses_detail(company, start, end):
		add("Purchase Invoice", d.doc_name, d.posting_date, d.party, "Purchase",
			_("Reverse charge (input)"), "input_vat_rcm", d.amount, d.vat_amount)

	return sorted(out, key=lambda r: (r["posting_date"], r["doc_name"]))


VAT_FILED_FIELD = "custom_vat_filed"  # Check field on Sales Invoice and Purchase Invoice
MARK_FILED_ON_JE = True  # tick custom_vat_filed on the selected vouchers when the Journal Entry is created


def _check_filed_field():
	missing = [
		dt for dt in ("Sales Invoice", "Purchase Invoice") if not frappe.get_meta(dt).has_field(VAT_FILED_FIELD)
	]
	if missing:
		frappe.throw(
			_("Please add a Check field named {0} to: {1}").format(VAT_FILED_FIELD, ", ".join(missing))
		)
	# the exclusion flag must exist on Sales Invoice, otherwise the report queries fail
	if not frappe.get_meta("Sales Invoice").has_field(EXCLUDE_SI_FIELD):
		frappe.throw(
			_("Please add a Check field named {0} to Sales Invoice (fetch from the Sales Taxes and Charges Template).").format(
				EXCLUDE_SI_FIELD
			)
		)
	# NEW: the item-level exclusion flag must exist on Purchase Invoice Item
	if not frappe.get_meta("Purchase Invoice Item").has_field(EXCLUDE_PI_ITEM_FIELD):
		frappe.throw(
			_("Please add a Check field named {0} to Purchase Invoice Item.").format(EXCLUDE_PI_ITEM_FIELD)
		)


def _filed_vouchers(rows):
	"""Set of (doctype, name) that already have custom_vat_filed ticked."""
	filed = set()
	for dt in ("Sales Invoice", "Purchase Invoice"):
		names = list({r["doc_name"] for r in rows if r["doc_type"] == dt})
		if names:
			for n in frappe.get_all(dt, filters={"name": ["in", names], VAT_FILED_FIELD: 1}, pluck="name"):
				filed.add((dt, n))
	return filed


def _build_vat_lines(totals, accounts):
	"""Journal Entry lines in two blocks, exactly like the accountant's format:

	  Output VAT            Dr
	  Output VAT RCM        Dr
	      VAT Payable             Cr   (total of the output block)

	  Input VAT                   Cr
	  Input VAT RCM               Cr
	  VAT Payable           Dr         (total of the input block)

	The two VAT Payable lines net to the VAT payable for the period. There is no separate
	"VAT Receivable" account: if input VAT is more than output VAT, VAT Payable simply ends
	with a debit (negative) balance, i.e. a refund is due."""
	lines = []

	def add(key, dr=0.0, cr=0.0):
		line = {"account": accounts[key]}
		if dr:
			line["debit_in_account_currency"] = dr
		if cr:
			line["credit_in_account_currency"] = cr
		lines.append(line)

	# ---- Block 1: output VAT (credit balance accounts -> debit to clear)
	out_net = 0.0  # debits minus credits of the block
	for key in ("output_vat", "output_vat_rcm"):
		amt = flt(totals.get(key, 0), 2)
		if amt > 0:
			add(key, dr=amt)
		elif amt < 0:
			add(key, cr=-amt)
		out_net += amt
	out_net = flt(out_net, 2)

	# ---- Block 2: input VAT (debit balance accounts -> credit to clear)
	in_net = 0.0  # credits minus debits of the block
	for key in ("input_vat", "input_vat_rcm"):
		amt = flt(totals.get(key, 0), 2)
		if amt > 0:
			add(key, cr=amt)
		elif amt < 0:
			add(key, dr=-amt)
		in_net += amt
	in_net = flt(in_net, 2)

	net = flt(out_net - in_net, 2)  # > 0 payable, < 0 refundable (negative VAT Payable)

	# VAT Payable line of the output block goes right after the output lines
	# (credit when output > 0), then the input block lines, then its VAT Payable line.
	out_lines = [l for l in lines if l["account"] in (accounts["output_vat"], accounts["output_vat_rcm"])]
	in_lines = [l for l in lines if l["account"] in (accounts["input_vat"], accounts["input_vat_rcm"])]
	lines = list(out_lines)
	if out_net > 0:
		add("vat_payable", cr=out_net)
	elif out_net < 0:
		add("vat_payable", dr=-out_net)
	lines.extend(in_lines)

	if in_net > 0:
		add("vat_payable", dr=in_net)
	elif in_net < 0:
		add("vat_payable", cr=-in_net)
	return lines, net


def _check_accounts(accounts):
	missing = [a for a in accounts if not frappe.db.exists("Account", a)]
	if missing:
		frappe.throw(
			_("These accounts were not found: {0}. Create them "
			"or correct VAT_ACCOUNT_NUMBERS in the report's Python file.").format(
				", ".join(missing)
			)
		)


@frappe.whitelist()
def create_vat_journal_entry(company, from_date, to_date, keys):
	"""Creates ONE draft Journal Entry for the selected transactions."""
	frappe.has_permission("Journal Entry", "create", throw=True)
	keys = json.loads(keys) if isinstance(keys, str) else keys
	if not keys:
		frappe.throw(_("Please select at least one transaction."))

	from_date, to_date = getdate(from_date), getdate(to_date)
	rows = {r["key"]: r for r in _all_vat_rows(company, from_date, to_date)}

	selected = []
	for k in keys:
		if k not in rows:
			frappe.throw(_("{0} is no longer available for this return. Please reload and select again.").format(k))
		selected.append(rows[k])

	_check_filed_field()
	filed = _filed_vouchers(selected)
	already = sorted({r["doc_name"] for r in selected if (r["doc_type"], r["doc_name"]) in filed})
	if already:
		frappe.throw(_("Already included in another return: {0}").format(", ".join(already)))

	totals = {}
	for r in selected:
		totals[r["bucket"]] = totals.get(r["bucket"], 0) + r["vat"]

	accounts = _vat_accounts(company)
	lines, net = _build_vat_lines(totals, accounts)
	if not lines:
		frappe.throw(_("The selected transactions have no VAT amount to post."))
	_check_accounts([l["account"] for l in lines])

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = company
	je.posting_date = to_date
	je.user_remark = "{0} {1} | {2} to {3}\nVouchers: {4}".format(
		VAT_JE_MARKER,
		company,
		from_date,
		to_date,
		", ".join(sorted({r["doc_name"] for r in selected})),
	)
	for l in lines:
		je.append("accounts", l)
	je.insert()  # stays in Draft so the accountant can review and submit

	if MARK_FILED_ON_JE:
		for dt, name in {(r["doc_type"], r["doc_name"]) for r in selected}:
			frappe.db.set_value(dt, name, VAT_FILED_FIELD, 1, update_modified=False)

	output = sum(flt(totals.get(k, 0)) for k in ("output_vat", "output_vat_rcm"))
	inp = sum(flt(totals.get(k, 0)) for k in ("input_vat", "input_vat_rcm"))
	return {
		"name": je.name,
		"output": flt(output, 2),
		"input": flt(inp, 2),
		"net": net,  # > 0 payable, < 0 refundable (VAT Payable goes negative)
	}


@frappe.whitelist()
def create_vat_settlement_entry(journal_entry, bank_account, posting_date, reference_no, reference_date):
	"""Payment of VAT Payable (Dr VAT Payable, Cr Bank) or, when the VAT Payable balance of the
	return is negative, receipt of the refund (Dr Bank, Cr VAT Payable) as a draft Bank Entry."""
	frappe.has_permission("Journal Entry", "create", throw=True)
	src = frappe.get_doc("Journal Entry", journal_entry)
	if not (src.user_remark or "").startswith(VAT_JE_MARKER) or src.docstatus == 2:
		frappe.throw(_("{0} is not a valid VAT Journal Entry.").format(journal_entry))

	marker = "{0} {1}".format(VAT_SETTLE_MARKER, src.name)
	if frappe.db.exists(
		"Journal Entry", {"docstatus": ["<", 2], "user_remark": ["like", marker + "%"]}
	):
		frappe.throw(_("A payment/refund entry already exists for {0}.").format(src.name))

	accounts = _vat_accounts(src.company)
	if frappe.db.get_value("Account", bank_account, "company") != src.company:
		frappe.throw(_("{0} does not belong to {1}.").format(bank_account, src.company))

	# credit - debit on VAT Payable: > 0 = amount to pay, < 0 = refund to receive
	payable = sum(
		flt(r.credit_in_account_currency) - flt(r.debit_in_account_currency)
		for r in src.accounts
		if r.account == accounts["vat_payable"]
	)

	if payable > 0:
		amount = flt(payable, 2)
		lines = [
			{"account": accounts["vat_payable"], "debit_in_account_currency": amount},
			{"account": bank_account, "credit_in_account_currency": amount},
		]
	elif payable < 0:
		amount = flt(-payable, 2)
		lines = [
			{"account": bank_account, "debit_in_account_currency": amount},
			{"account": accounts["vat_payable"], "credit_in_account_currency": amount},
		]
	else:
		frappe.throw(_("There is no VAT payable or refundable to settle in {0}.").format(src.name))

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Bank Entry"
	je.company = src.company
	je.posting_date = getdate(posting_date)
	je.cheque_no = reference_no
	je.cheque_date = getdate(reference_date)
	je.user_remark = "{0}\nVAT payment/refund for {1}".format(marker, src.name)
	for l in lines:
		je.append("accounts", l)
	je.insert()
	return je.name
