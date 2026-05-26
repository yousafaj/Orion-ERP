import frappe
from frappe import _
from frappe.core.doctype.doctype.doctype import (
	clear_permissions_cache,
	validate_permissions_for_doctype,
)
from frappe.exceptions import DoesNotExistError
from frappe.modules.import_file import get_file_path, read_doc_from_file
from frappe.permissions import (
	AUTOMATIC_ROLES,
	add_permission,
	get_all_perms,
	get_linked_doctypes,
	reset_perms,
	setup_custom_perms,
	update_permission_property,
)
from frappe.utils.user import get_users_with_role as _get_users_with_role

not_allowed_in_permission_manager = ["DocType", "Patch Log", "Module Def", "Transaction Log"]


def _is_allowed():
	if "System Manager" in frappe.get_roles():
		return True
	allowed_roles = frappe.get_all("Role Details",
		filters={"parent": "Orion Settings", "parentfield": "allowed_roles"},
		pluck="role")
	return bool(set(allowed_roles) & set(frappe.get_roles()))


def _check_permission():
	if not _is_allowed():
		frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_roles_and_doctypes():
	_check_permission()

	active_domains = frappe.get_active_domains()

	doctypes = frappe.get_all(
		"DocType",
		filters={
			"istable": 0,
			"name": ("not in", ",".join(not_allowed_in_permission_manager)),
		},
		or_filters={"ifnull(restrict_to_domain, '')": "", "restrict_to_domain": ("in", active_domains)},
		fields=["name"],
	)

	restricted_roles = ["Administrator"]
	if frappe.session.user != "Administrator":
		custom_user_type_roles = frappe.get_all("User Type", filters={"is_standard": 0}, fields=["role"])
		restricted_roles.extend(row.role for row in custom_user_type_roles)
		restricted_roles.extend(AUTOMATIC_ROLES)

	roles = frappe.get_all(
		"Role",
		filters={
			"name": ("not in", restricted_roles),
			"disabled": 0,
		},
		or_filters={"ifnull(restrict_to_domain, '')": "", "restrict_to_domain": ("in", active_domains)},
		fields=["name"],
	)

	doctypes_list = [{"label": _(d.get("name")), "value": d.get("name")} for d in doctypes]
	roles_list = [{"label": _(d.get("name")), "value": d.get("name")} for d in roles]

	return {
		"doctypes": sorted(doctypes_list, key=lambda d: d["label"].casefold()),
		"roles": sorted(roles_list, key=lambda d: d["label"].casefold()),
	}


@frappe.whitelist()
def get_permissions(doctype: str | None = None, role: str | None = None):
	_check_permission()

	if role:
		out = get_all_perms(role)
		if doctype:
			out = [p for p in out if p.parent == doctype]
	else:
		filters = {"parent": doctype}
		if frappe.session.user != "Administrator":
			custom_roles = frappe.get_all("Role", filters={"is_custom": 1}, pluck="name")
			filters["role"] = ["not in", custom_roles]

		out = frappe.get_all("Custom DocPerm", fields="*", filters=filters, order_by="permlevel")
		if not out:
			out = frappe.get_all("DocPerm", fields="*", filters=filters, order_by="permlevel")

	linked_doctypes = {}
	for d in out:
		if d.parent not in linked_doctypes:
			try:
				linked_doctypes[d.parent] = get_linked_doctypes(d.parent)
			except DoesNotExistError:
				frappe.clear_last_message()
				continue
		d.linked_doctypes = linked_doctypes[d.parent]
		if meta := frappe.get_meta(d.parent):
			d.is_submittable = meta.is_submittable
			d.in_create = meta.in_create

	return out


@frappe.whitelist()
def add(parent, role, permlevel):
	_check_permission()
	add_permission(parent, role, permlevel)


@frappe.whitelist()
def update(doctype, role, permlevel, ptype, value=None, if_owner=0):
	def clear_cache():
		frappe.clear_cache(doctype=doctype)

	_check_permission()

	if ptype == "report" and value == "1" and if_owner == "1":
		frappe.throw(_("Cannot set 'Report' permission if 'Only If Creator' permission is set"))

	out = update_permission_property(doctype, role, permlevel, ptype, value, if_owner=if_owner)

	if ptype == "if_owner" and value == "1":
		update_permission_property(doctype, role, permlevel, "report", "0", if_owner=value)

	frappe.db.after_commit.add(clear_cache)

	return "refresh" if out else None


@frappe.whitelist()
def remove(doctype, role, permlevel, if_owner=0):
	_check_permission()
	setup_custom_perms(doctype)

	frappe.db.delete(
		"Custom DocPerm",
		{"parent": doctype, "role": role, "permlevel": permlevel, "if_owner": if_owner},
	)

	if not frappe.get_all("Custom DocPerm", {"parent": doctype}):
		frappe.throw(_("There must be atleast one permission rule."), title=_("Cannot Remove"))

	validate_permissions_for_doctype(doctype, for_remove=True, alert=True)


@frappe.whitelist()
def reset(doctype):
	_check_permission()
	reset_perms(doctype)
	clear_permissions_cache(doctype)


@frappe.whitelist()
def get_users_with_role(role):
	_check_permission()
	return _get_users_with_role(role)


@frappe.whitelist()
def get_standard_permissions(doctype):
	_check_permission()
	meta = frappe.get_meta(doctype)
	if meta.custom:
		doc = frappe.get_doc("DocType", doctype)
		return [p.as_dict() for p in doc.permissions]
	else:
		path = get_file_path(meta.module, "DocType", doctype)
		return read_doc_from_file(path).get("permissions")
