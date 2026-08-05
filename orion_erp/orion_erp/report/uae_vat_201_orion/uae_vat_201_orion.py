# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import re

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}
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
		       si.debit_to AS receivable_account
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
	cond = "AND si.docstatus = 1"
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

	return frappe.db.sql(
		f"""
		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
		       pi.supplier_name AS party, '' AS item,
		       pi.base_total AS amount, SUM(gl.debit) AS vat_amount
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

	return frappe.db.sql(
		f"""
		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
		       pi.supplier_name AS party, '' AS item,
		       pi.base_total AS amount, pi.recoverable_standard_rated_expenses AS vat_amount
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

	return frappe.db.sql(
		f"""
		SELECT pi.posting_date, pi.name AS doc_name, 'Purchase Invoice' AS doc_type,
		       pi.supplier_name AS party, '' AS item,
		       pi.base_total AS amount,
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
	if filters.get("from_date"):
		query_filters.append(["posting_date", "<=", filters["to_date"]])
	return query_filters


def get_reverse_charge_total(filters):
	query_filters = get_filters(filters)
	query_filters.append(["reverse_charge", "=", "Y"])
	query_filters.append(["docstatus", "=", 1])
	try:
		return (
			frappe.db.get_all(
				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
			)[0][0]
			or 0
		)
	except (IndexError, TypeError):
		return 0


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


def get_reverse_charge_recoverable_total(filters):
	query_filters = get_filters(filters)
	query_filters.append(["reverse_charge", "=", "Y"])
	query_filters.append(["recoverable_reverse_charge", ">", "0"])
	query_filters.append(["docstatus", "=", 1])
	try:
		return (
			frappe.db.get_all(
				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
			)[0][0]
			or 0
		)
	except (IndexError, TypeError):
		return 0


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


def get_standard_rated_expenses_total(filters):
	query_filters = get_filters(filters)
	query_filters.append(["recoverable_standard_rated_expenses", ">", 0])
	query_filters.append(["docstatus", "=", 1])
	try:
		return (
			frappe.db.get_all(
				"Purchase Invoice", filters=query_filters, fields=["sum(base_total)"], as_list=True, limit=1
			)[0][0]
			or 0
		)
	except (IndexError, TypeError):
		return 0


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
	conditions = ""
	for opts in (
		("company", " and company=%(company)s"),
		("from_date", " and posting_date>=%(from_date)s"),
		("to_date", " and posting_date<=%(to_date)s"),
	):
		if filters.get(opts[0]):
			conditions += opts[1]
	return conditions
