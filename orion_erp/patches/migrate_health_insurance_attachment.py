import frappe


def execute():
	"""Copy Health Insurance attachment (Attach Image) data into the Health
	Insurance attach (Attach) field on Employee."""
	if not _column_exists("Employee", "custom_health_insurance_attachment"):
		return
	if not _column_exists("Employee", "custom_health_insurance_attach"):
		return

	rows = frappe.db.sql(
		"""
		SELECT name, custom_health_insurance_attachment
		FROM `tabEmployee`
		WHERE custom_health_insurance_attachment IS NOT NULL
		AND custom_health_insurance_attachment != ''
		AND (custom_health_insurance_attach IS NULL OR custom_health_insurance_attach = '')
		""",
		as_dict=True,
	)

	for row in rows:
		frappe.db.set_value(
			"Employee",
			row.name,
			"custom_health_insurance_attach",
			row.custom_health_insurance_attachment,
		)


def _column_exists(doctype, column):
	columns = frappe.db.sql(f"SHOW COLUMNS FROM `tab{doctype}` LIKE '{column}'")
	return bool(columns)
