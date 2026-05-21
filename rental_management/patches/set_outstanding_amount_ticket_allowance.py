import frappe
from frappe.utils import flt


def execute():

	ticket_allowance_details = frappe.get_all(
		"Ticket Allowance Detail",
		filters={
			"manual_paid": 0
		},
		fields=[
			"name",
			"amount"
		]
	)

	for row in ticket_allowance_details:

		amount = flt(row.amount)

		frappe.db.set_value(
			"Ticket Allowance Detail",
			row.name,
			{
				"outstanding_amount": amount
			}
		)
