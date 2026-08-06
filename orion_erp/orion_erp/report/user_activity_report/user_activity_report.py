# Copyright (c) 2026, NDDB and contributors
# For license information, please see license.txt


import frappe
from frappe.utils import getdate, flt, add_days, nowdate
from datetime import datetime, time
import json


def execute(filters=None):
	columns, data = [], []
	data, child_data = get_data(filters)
	if child_data:
		columns = get_columns()
	else:
		columns = get_no_child_columns()
	return columns, data

def get_columns():
	return [
        {"label": "Change ID", "fieldname": "change_id", "fieldtype": "Link", "options": "Version", "width": 150},
        {"label": "Date & Time", "fieldname": "date_and_time", "fieldtype": "Data", "width": 200},
        {"label": "User ID", "fieldname": "user_id", "fieldtype": "Link", "options": "User", "width": 200},
        {"label": "User Name", "fieldname": "user_name", "fieldtype": "Data", "width": 200},
        {"label": "DocType", "fieldname": "doctype", "fieldtype": "Data", "width": 200},
        {"label": "System Manager Role", "fieldname": "system_manager_role", "fieldtype": "Data", "width": 160},
        {"label": "Change Type", "fieldname": "change_type", "fieldtype": "Data", "width": 200},
        {"label": "Field Label", "fieldname": "field_label", "fieldtype": "Data", "width": 300},
        {"label": "Old Value", "fieldname": "old_value", "fieldtype": "Data", "width": 200},
        {"label": "New Value", "fieldname": "new_value", "fieldtype": "Data", "width": 200},
		{"label": "Child Table", "fieldname": "child_table", "fieldtype": "Data", "width": 200},
        {"label": "Row Index", "fieldname": "row_index", "fieldtype": "Data", "width": 100},
	]

def get_no_child_columns():
	return [
        {"label": "Change ID", "fieldname": "change_id", "fieldtype": "Link", "options": "Version", "width": 150},
        {"label": "Date & Time", "fieldname": "date_and_time", "fieldtype": "Data", "width": 200},
        {"label": "User ID", "fieldname": "user_id", "fieldtype": "Link", "options": "User", "width": 200},
        {"label": "User Name", "fieldname": "user_name", "fieldtype": "Data", "width": 200},
        {"label": "DocType", "fieldname": "doctype", "fieldtype": "Data", "width": 200},
        {"label": "System Manager Role", "fieldname": "system_manager_role", "fieldtype": "Data", "width": 160},
        {"label": "Change Type", "fieldname": "change_type", "fieldtype": "Data", "width": 200},
        {"label": "Field Label", "fieldname": "field_label", "fieldtype": "Data", "width": 300},
        {"label": "Old Value", "fieldname": "old_value", "fieldtype": "Data", "width": 200},
        {"label": "New Value", "fieldname": "new_value", "fieldtype": "Data", "width": 200},
	]

def get_data(filters):
	conditions = []
	values = {}

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	user = filters.get("user")
	doctype = filters.get("doctype")
	module = filters.get("module")
	fieldname = filters.get("fieldname")
	if fieldname:
		fieldname = frappe.db.get_value("DocField", fieldname, "fieldname")
	change_type = filters.get("change_type")

	# ---------------- Optional Filters ----------------
	orion_settings = frappe.get_doc("Orion Settings")
	allowed_backdated_range_limit_days = orion_settings.allowed_backdated_range_limit_days or 0

	if orion_settings.enable_tic_report_configuration and allowed_backdated_range_limit_days > 0:
		configured_date = add_days(nowdate(), -flt(allowed_backdated_range_limit_days))
	else:
		configured_date = None

	if configured_date and from_date:
		if getdate(from_date) <= getdate(configured_date):
			conditions.append("DATE(ver.creation) >= %(from_date)s")
			values["from_date"] = getdate(configured_date)
		else:
			conditions.append("DATE(ver.creation) >= %(from_date)s")
			values["from_date"] = getdate(from_date)
	elif from_date:
		conditions.append("DATE(ver.creation) >= %(from_date)s")
		values["from_date"] = getdate(from_date)

	if to_date:
		conditions.append("DATE(ver.creation) <= %(to_date)s")
		values["to_date"] = getdate(to_date)

	if user:
		conditions.append("ver.owner = %(user)s")
		values["user"] = user

	if doctype:
		conditions.append("ver.ref_doctype = %(doctype)s")
		values["doctype"] = doctype
	else:
		# Filter: only doctypes with "Settings" in name
		conditions.append("doc.name LIKE %(settings_filter)s")
		values["settings_filter"] = "%Setting%"

	if module:
		conditions.append("mod_def.name = %(module)s")
		values["module"] = module

	# ---------------- Build WHERE Clause ----------------
	condition_sql = ""
	if conditions:
		condition_sql = " AND " + " AND ".join(conditions)

	query = f"""
		SELECT
			ver.name AS change_id,
			ver.creation AS date_and_time,
			ver.owner AS user_id,
			ver.ref_doctype AS doctype,
			ver.docname AS document_name,
			ver.data AS field_data
		FROM `tabVersion` ver
		LEFT JOIN `tabDocType` doc
			ON ver.ref_doctype = doc.name
		LEFT JOIN `tabModule Def` mod_def
			ON doc.module = mod_def.name
		WHERE
			1=1
			{condition_sql}
		ORDER BY ver.creation, ver.ref_doctype
	"""

	data = frappe.db.sql(query, values, as_dict=True)

	formatted_data = get_formatted_data(data)

	result = get_final_result(formatted_data, fieldname, change_type)

	return result

def get_formatted_data(data):
	formatted_data = []

	for row in data:
		date_and_time = row.date_and_time
		user_id = row.user_id

		# Format date and time to dd-mm-yyyy hh:mm-ss
		if date_and_time:
			row.date_and_time = date_and_time.strftime("%d-%m-%Y / %H:%M:%S")

		# Get User's name using User ID
		if user_id:
			username = frappe.db.get_value("User", user_id, "full_name")
			row.user_name = username

		# Check user has system manager role or not
		if user_id == "Administrator":
			row.system_manager_role = "YES"
		elif user_id:
			user_roles = frappe.get_roles(user_id)
			if "System Manager" in user_roles:
				row.system_manager_role = "YES"
			else:
				row.system_manager_role = "NO"

		# Extract field label, old value and new value from data
		field_data = row.field_data
		if field_data:
			field_data = json.loads(field_data)
		row["field_data"] = field_data

		# Append formatted row
		formatted_data.append(row)
	return formatted_data

def get_final_result(formatted_data, fieldname=None, change_type=None):
	result = []
	child_data = False
	for detail in formatted_data:
		doctype = detail.get("doctype")
		field_data = detail.field_data
		for key, value in field_data.items():
			if key == "added":
				for item in value:
					field_name = item[0]
					meta = frappe.get_meta(doctype)
					field_label = meta.get_label(field_name)
					df = meta.get_field(field_name)
					if df.fieldtype == "Table" or df.fieldtype == "Table MultiSelect":
						field_name, row_data = item
						if fieldname and fieldname != field_name:
							continue
						if change_type and change_type in ["Delete","Update"]:
							continue
						child_doctype = df.options
						child_meta = frappe.get_meta(child_doctype)
						row_idx = row_data.get("idx")
						for child_field, val in row_data.items():
							if child_field in ("name", "owner", "creation", "modified", "doctype",
											"modified_by", "parent", "parentfield",
											"parenttype", "idx", "docstatus", "__unsaved"):
								continue
							child_df = child_meta.get_field(child_field)
							child_label = child_df.label if child_df else child_field
							row_wise_data = {
								"change_id" : detail.get("change_id"),
								"date_and_time" : detail.get("date_and_time"),
								"user_id" : detail.get("user_id"),
								"doctype" : detail.get("doctype"),
								"document_name" : detail.get("document_name"),
								"user_name" : detail.get("user_name"),
								"system_manager_role" : detail.get("system_manager_role"),
								"child_table": field_label,
								"row_index": row_idx,
								"field_label" : child_label,
								"old_value" : val,
								"new_value" : None,
								"change_type" : "Insert"
							}
							result.append(row_wise_data)
							child_data = True
					else:
						field_name, old_value, new_value = item
						if fieldname and fieldname != field_name:
							continue
						if change_type and change_type in ["Delete","Update"]:
							continue
						row_wise_data = {
							"change_id" : detail.get("change_id"),
							"date_and_time" : detail.get("date_and_time"),
							"user_id" : detail.get("user_id"),
							"doctype" : detail.get("doctype"),
							"document_name" : detail.get("document_name"),
							"user_name" : detail.get("user_name"),
							"system_manager_role" : detail.get("system_manager_role"),
							"field_label" : field_label,
							"old_value" : old_value,
							"new_value" : new_value,
							"change_type" : "Insert"
						}
						result.append(row_wise_data)

			if key == "changed":
				for item in value:
					field_name = item[0]
					meta = frappe.get_meta(doctype)
					field_label = meta.get_label(field_name)
					df = meta.get_field(field_name)
					field_name, old_value, new_value = item
					if fieldname and fieldname != field_name:
						continue
					if change_type and change_type in ["Insert","Delete"]:
						continue
					row_wise_data = {
						"change_id" : detail.get("change_id"),
						"date_and_time" : detail.get("date_and_time"),
						"user_id" : detail.get("user_id"),
						"doctype" : detail.get("doctype"),
						"document_name" : detail.get("document_name"),
						"user_name" : detail.get("user_name"),
						"system_manager_role" : detail.get("system_manager_role"),
						"field_label" : field_label,
						"old_value" : old_value,
						"new_value" : new_value,
						"change_type" : "Update"
					}
					result.append(row_wise_data)

			if key == "removed":
				for item in value:
					field_name = item[0]
					meta = frappe.get_meta(doctype)
					field_label = meta.get_label(field_name)
					df = meta.get_field(field_name)
					if df.fieldtype == "Table" or df.fieldtype == "Table MultiSelect":
						field_name, row_data = item
						if fieldname and fieldname != field_name:
							continue
						if change_type and change_type in ["Insert","Update"]:
							continue
						child_doctype = df.options
						child_meta = frappe.get_meta(child_doctype)
						row_idx = row_data.get("idx")
						for child_field, val in row_data.items():
							if child_field in ("name", "owner", "creation", "modified", "doctype",
											"modified_by", "parent", "parentfield",
											"parenttype", "idx", "docstatus", "__unsaved"):
								continue
							child_df = child_meta.get_field(child_field)
							child_label = child_df.label if child_df else child_field
							row_wise_data = {
								"change_id" : detail.get("change_id"),
								"date_and_time" : detail.get("date_and_time"),
								"user_id" : detail.get("user_id"),
								"doctype" : detail.get("doctype"),
								"document_name" : detail.get("document_name"),
								"user_name" : detail.get("user_name"),
								"system_manager_role" : detail.get("system_manager_role"),
								"child_table": field_label,
								"row_index": row_idx,
								"field_label" : child_label,
								"old_value" : val,
								"new_value" : None,
								"change_type" : "Delete"
							}
							result.append(row_wise_data)
							child_data = True
					else:
						field_name, old_value, new_value = item
						if fieldname and fieldname != field_name:
							continue
						if change_type and change_type in ["Insert","Update"]:
							continue
						row_wise_data = {
							"change_id" : detail.get("change_id"),
							"date_and_time" : detail.get("date_and_time"),
							"user_id" : detail.get("user_id"),
							"doctype" : detail.get("doctype"),
							"document_name" : detail.get("document_name"),
							"user_name" : detail.get("user_name"),
							"system_manager_role" : detail.get("system_manager_role"),
							"field_label" : field_label,
							"old_value" : old_value,
							"new_value" : new_value,
							"change_type" : "Delete"
						}
						result.append(row_wise_data)

			if key == "row_changed":
				for item in value:
					field_name = item[0]
					meta = frappe.get_meta(doctype)
					field_label = meta.get_label(field_name)
					df = meta.get_field(field_name)
					if df.fieldtype == "Table":
						child_doc_name, row_num, child_name, child_row_data = item
						if fieldname and fieldname != field_name:
							continue
						if change_type and change_type in ["Insert","Delete"]:
							continue
						child_doctype = df.options
						child_meta = frappe.get_meta(child_doctype)
						for item in child_row_data:
							child_field_name, child_old_value, child_new_value = item
							child_df = child_meta.get_field(child_field_name)
							child_label = child_df.label if child_df else child_field

							row_wise_data = {
								"change_id" : detail.get("change_id"),
								"date_and_time" : detail.get("date_and_time"),
								"user_id" : detail.get("user_id"),
								"doctype" : detail.get("doctype"),
								"document_name" : detail.get("document_name"),
								"user_name" : detail.get("user_name"),
								"system_manager_role" : detail.get("system_manager_role"),
								"child_table": field_label,
								"row_index": flt(row_num) + 1,
								"field_label" : child_label,
								"old_value" : child_old_value,
								"new_value" : child_new_value,
								"change_type" : "Update"
							}
							result.append(row_wise_data)
							child_data = True
	return result, child_data


@frappe.whitelist()
def get_docfield_options(doctype, txt, searchfield, start, page_len, filters):
	doctype_selected = filters.get("doctype")
	if doctype_selected:
		return frappe.db.sql("""
			SELECT name, label
			FROM `tabDocField`
			WHERE parent = %s
			AND (fieldname LIKE %s OR label LIKE %s)
			LIMIT %s OFFSET %s
		""", (doctype_selected, f"%{txt}%", f"%{txt}%", page_len, start))
	else:
		return []

@frappe.whitelist()
def get_field_label(fieldname):
    return frappe.db.get_value("DocField", fieldname, "label", ignore_permissions=True)

@frappe.whitelist()
def get_module_from_doctype(doctype, txt, searchfield, start, page_len, filters):
    doctype_selected = filters.get("doctype")
    module = frappe.db.get_value("DocType", doctype_selected, "module")

    if module:
        return [(module,)]
    return []
