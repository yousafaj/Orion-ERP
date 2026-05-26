# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from frappe.permissions import add_permission, update_permission_property, setup_custom_perms


class OrionSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from orion_erp.orion_erp.doctype.role_details.role_details import RoleDetails
		from orion_erp.orion_erp.doctype.ticket_entitlement.ticket_entitlement import TicketEntitlement

		allowed_roles: DF.TableMultiSelect[RoleDetails]
		company_logo: DF.AttachImage | None
		cron_schedule_date_noe: DF.Date | None
		cron_schedule_date_oe: DF.Date | None
		default_bank_name_for_c3_pay: DF.Data | None
		last_month_for_which_payment_processed_noe: DF.Date | None
		last_month_for_which_payment_processed_oe: DF.Date | None
		manual_paid_check_read_only_date: DF.Date | None
		payroll_month_date_noe: DF.Date | None
		payroll_month_date_oe: DF.Date | None
		role_for_non_office_employee_ssa_access: DF.TableMultiSelect[RoleDetails]
		show_trigger_additional_deduction_non_office: DF.Check
		show_trigger_additional_deduction_office: DF.Check
		ss_print_logo: DF.AttachImage | None
		ticket_entitlement_detail: DF.Table[TicketEntitlement]
		vehicle_handover_image: DF.AttachImage | None
	# end: auto-generated types

	def on_update(self):
		sync_role_permissions()


def sync_role_permissions():
	doctype = "Role Permission for Page and Report"
	allowed_roles = frappe.get_all("Role Details", filters={"parent": "Orion Settings", "parentfield": "allowed_roles"}, pluck="role")

	setup_custom_perms(doctype)

	existing_roles = set(frappe.get_all("Custom DocPerm", filters={"parent": doctype}, pluck="role"))
	roles_to_remove = existing_roles - set(allowed_roles) - {"System Manager"}

	for role in roles_to_remove:
		frappe.db.delete("Custom DocPerm", {"parent": doctype, "role": role})

	if not allowed_roles:
		return

	full_access = {
		"select": 1, "read": 1, "write": 1, "create": 1, "delete": 1,
		"print": 1, "email": 1, "report": 1, "import": 1, "export": 1, "share": 1,
	}

	for role in allowed_roles:
		add_permission(doctype, role)
		for ptype, value in full_access.items():
			update_permission_property(doctype, role, permlevel=0, ptype=ptype, value=value)

	grant_permission_manager_access(allowed_roles)


def grant_permission_manager_access(roles):
	custom_role_name = frappe.db.get_value("Custom Role", {"page": "permission-manager"})
	role_list = [{"role": r} for r in roles]

	if custom_role_name:
		custom_role = frappe.get_doc("Custom Role", custom_role_name)
		custom_role.set("roles", role_list)
		custom_role.save(ignore_permissions=True)
	else:
		frappe.get_doc({
			"doctype": "Custom Role",
			"page": "permission-manager",
			"roles": role_list,
		}).insert(ignore_permissions=True)
