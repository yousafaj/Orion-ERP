import frappe
from orion_erp.orion_erp.doctype.orion_settings.orion_settings import sync_role_permissions
from orion_erp.orion_erp.validations.cicpa_dashboard import setup_cicpa_workspace_widgets


def after_migrate():
    sync_role_permissions()
    setup_cicpa_workspace_widgets()

