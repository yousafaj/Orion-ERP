import frappe
from orion_erp.orion_erp.doctype.orion_settings.orion_settings import sync_role_permissions


def after_migrate():
    sync_role_permissions()
