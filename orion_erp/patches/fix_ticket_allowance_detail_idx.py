import frappe


def execute():

	employees = frappe.db.sql("""
		SELECT DISTINCT parent
		FROM `tabTicket Allowance Detail`
		WHERE parenttype = 'Employee'
		ORDER BY parent
	""", as_dict=True)

	for emp in employees:

		records = frappe.db.sql("""
			SELECT name, from_date, idx
			FROM `tabTicket Allowance Detail`
			WHERE parent = %(parent)s AND parenttype = 'Employee'
			ORDER BY from_date ASC, creation ASC
		""", {"parent": emp.parent}, as_dict=True)

		if not records:
			continue

		needs_fix = any(r.idx != i + 1 for i, r in enumerate(records))

		if needs_fix:

			for i, r in enumerate(records):

				new_idx = i + 1

				if r.idx != new_idx:

					frappe.db.set_value(
						"Ticket Allowance Detail",
						r.name,
						"idx",
						new_idx,
						update_modified=False
					)
