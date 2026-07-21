app_name = "orion_erp"
app_title = "Orion ERP"
app_publisher = "osama.ahmed@deliverydevs.com"
app_description = "One stop solution to manage vehicle rentals"
app_email = "osama.ahmed@deliverydevs.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "orion_erp",
# 		"logo": "/assets/orion_erp/logo.png",
# 		"title": "Orion ERP",
# 		"route": "/orion_erp",
# 		"has_permission": "orion_erp.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/orion_erp/css/orion_erp.css"

# include js, css files in header of web template
# web_include_css = "/assets/orion_erp/css/orion_erp.css"
# web_include_js = "/assets/orion_erp/js/orion_erp.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "orion_erp/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Employee" : "public/js/employee.js",
    "Additional Salary": "public/js/additional_salary.js",
    "Leave Application": "public/js/leave_application.js",
    "Salary Slip": "public/js/salary_slip.js",
    "Job Offer":"public/js/job_offer.js",
    "Driver": "public/js/driver.js",
    "Quotation": "public/js/quotation.js",
    "Leave Allocation": "public/js/leave_allocation.js",
    "Rejoining Form": "public/js/rejoining_form.js"
    }

# app_include_css = "/assets/orion_erp/css/listview.css"
doctype_list_js = {"Employee": "public/js/employee_list.js",
                   "Leave Application": "public/js/leave_application_list.js",
                   "Rejoining Form": "public/js/rejoining_form_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "orion_erp/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "orion_erp.utils.jinja_methods",
# 	"filters": "orion_erp.utils.jinja_filters"
# }

jinja = {
	"methods": [
        "orion_erp.orion_erp.scripts.jinja.get_qr_code",
        "orion_erp.api.get_company_logo"
    ],
	# "filters": "orion_erp.utils.jinja_filters
}

fixtures = [
    {
        "doctype": "Number Card",
        "filters": [
            ["name", "in", ["Total Employees"]]
        ]
    },
    {
        "doctype": "Role",
        "filters": [["name", "in", ["PRO"]]]
    },
    {
        "doctype": "Weekday",
        "filters": [
            ["name", "in", ["Saturday", "Sunday"]]
        ]
    }
]

# Installation
# ------------

# before_install = "orion_erp.install.before_install"
# after_install = "orion_erp.install.after_install"

after_install = "orion_erp.passport_management.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "orion_erp.uninstall.before_uninstall"
# after_uninstall = "orion_erp.uninstall.after_uninstall"

after_migrate = ["orion_erp.setup.after_migrate"]


# Testing
# -------
# Bootstrap erpnext/hrms standard fixtures (Warehouse Types like "Transit", the
# territory/customer-group trees, default UOMs, a test Company) before orion_erp
# tests run on a fresh site. Only invoked by the test runner.
before_tests = "hrms.tests.test_utils.before_tests"


# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "orion_erp.utils.before_app_install"
# after_app_install = "orion_erp.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "orion_erp.utils.before_app_uninstall"
# after_app_uninstall = "orion_erp.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "orion_erp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways
permission_query_conditions = {
    "Additional Salary": "orion_erp.orion_erp.permission_query.additonal_salary.get_additional_salary_permission_query",
	"Salary Structure Assignment": "orion_erp.orion_erp.permission_query.salary_structure_assignment.get_ssa_permission_query",
    "Leave Application":
    "orion_erp.orion_erp.permission_query.leave_application.leave_application_query",
    "Rejoining Form":
    "orion_erp.orion_erp.permission_query.rejoining_form.rejoining_form_query"
}
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }
# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

doc_events = {
    "Leave Application":{
         "validate":[
              "orion_erp.orion_erp.validations.leave_application.validate_leave_approval",
              "orion_erp.orion_erp.validations.leave_application.validate_annual_leave_avail",
              "orion_erp.orion_erp.validations.leave_application.validate_hajj_umrah_leave",
               "orion_erp.orion_erp.validations.leave_application.validate_medical_certificate",
               "orion_erp.orion_erp.validations.leave_application.validate_paternity_leave",
               "orion_erp.orion_erp.validations.leave_application.reset_status_on_amend",
               "orion_erp.orion_erp.services.leave_delegation.auto_delegate_leave_application"
         ],

        "on_update":[
            "orion_erp.orion_erp.validations.leave_application.handle_leave_approval",
            "orion_erp.orion_erp.services.leave_delegation.handle_auto_delegation_on_update"
        ],
        "on_submit":[
            "orion_erp.orion_erp.validations.leave_application.on_submit_leave_application"
        ],
        "on_cancel":[
            "orion_erp.orion_erp.validations.leave_application.on_cancel_leave_application"
        ]
    },
    "Rejoining Form":{
        "validate":[
            "orion_erp.orion_erp.validations.rejoining_form.validate_rejoining_approval",
            "orion_erp.orion_erp.validations.rejoining_form.reset_status_on_amend"
        ],
        "on_update":[
            "orion_erp.orion_erp.validations.rejoining_form.handle_rejoining_approval"
        ],
        "on_submit":[
            "orion_erp.orion_erp.validations.rejoining_form.on_submit_rejoining_form"
        ],
        "on_cancel":[
            "orion_erp.orion_erp.validations.rejoining_form.on_cancel_rejoining_form"
        ]
    },
    "Salary Structure Assignment":{
        "validate":"orion_erp.orion_erp.validations.salary_structure_assignment.validate_ssa_employee_category"
    },
    "Additional Salary":{
        "autoname":"orion_erp.orion_erp.services.additional_salary.autoname",
        "validate":"orion_erp.orion_erp.services.additional_salary.validate",
        "on_submit":"orion_erp.orion_erp.services.additional_salary.on_submit",
        "on_cancel":"orion_erp.orion_erp.services.additional_salary.on_cancel"
    },

    "Vehicle": {
        "validate": "orion_erp.orion_erp.validations.vehicle_hooks.validate_vehicle"
    },
    "Driver": {
        "validate": "orion_erp.orion_erp.validations.driver_hooks.validate_driver",
        "after_insert": "orion_erp.orion_erp.validations.driver_hooks.after_insert_driver"
    },
    "Customer": {
        "validate": "orion_erp.orion_erp.validations.customer_hooks.validate_customer"
    },
    "Employee": {
        "validate": ["orion_erp.orion_erp.validations.employee_hooks.validate_employee",
                    "orion_erp.orion_erp.services.employee.validate_allowance_amounts"],
        "after_insert": "orion_erp.orion_erp.services.employee.create_salary_structure_assignment",
        "on_update": [
            "orion_erp.orion_erp.services.employee.create_salary_structure_assignment",
            "orion_erp.orion_erp.services.employee.create_leave_policy_assignment",
            "orion_erp.orion_erp.services.employee.auto_allocate_hajj_umrah"
        ]
    },
    "Asset": {
        "autoname": "orion_erp.orion_erp.scripts.autoname_assets.autoname_asset"
    },
    "Leave Type": {
        "validate": [
              "orion_erp.orion_erp.validations.leave_type.validate_no_casual_leave",
              "orion_erp.orion_erp.validations.leave_type.validate_earned_leave_not_with_accrual"
         ]
    },
    "Leave Encashment": {
        "validate": "orion_erp.orion_erp.validations.leave_encashment.validate_leave_encashment",
        "on_cancel": "orion_erp.orion_erp.validations.leave_encashment.on_cancel_leave_encashment"
    },
    "Leave Allocation": {
        "before_submit": "orion_erp.orion_erp.scripts.leave_allocation_validation.before_submit"
    },
    "Payroll Entry": {
        "validate": "orion_erp.orion_erp.validations.payroll_medical_certificate.validate_medical_certificate_for_payroll_entry"
    },
    "Salary Slip": {
        "validate": "orion_erp.orion_erp.validations.payroll_medical_certificate.validate_medical_certificate_for_salary_slip"
    },
    "File": {
        "on_update": "orion_erp.orion_erp.validations.leave_application.update_medical_certificate_status_on_file_attach",
        "on_trash": "orion_erp.orion_erp.validations.leave_application.reset_medical_certificate_status_on_file_trash"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"orion_erp.tasks.all"
	# ],
    "cron": {
        "0 6 30 * *": [
            "orion_erp.orion_erp.services.additional_salary.create_monthly_allowances"
        ],
        # 1st of every month, 02:00 — build last month's Monthly Billing sheets so
        # Accounts never miss invoicing a customer-month.
        "0 2 1 * *": [
            "orion_erp.orion_erp.doctype.monthly_billing.monthly_billing.create_monthly_billing_sheets"
        ],
        # Run every minute to check leave application escalation status
        "* * * * *": [
            "orion_erp.orion_erp.scripts.leave_escalation.process_leave_escalations"
        ]
    },
	"daily": [
        # "orion_erp.orion_erp.services.employee_deduction.run_deduction_cron"
		"orion_erp.tasks.daily.daily",
        "orion_erp.orion_erp.scripts.certificate_notification.certificate_expiry_notification",
        "orion_erp.orion_erp.services.employee.create_ticket_allowance",
        "orion_erp.orion_erp.services.leave_delegation.restore_delegations",
        "orion_erp.passport_management.tasks.send_overdue_passport_alerts",
        "orion_erp.orion_erp.services.cicpa.auto_expire_cicpas",
        "orion_erp.orion_erp.services.loa.auto_expire_loas",
        "orion_erp.orion_erp.services.employee.auto_renew_leave_policy_assignments",
        "orion_erp.orion_erp.scripts.hajj_umrah_allocation.allocate_hajj_umrah_yearly_for_all",
        "orion_erp.orion_erp.scripts.annual_leave_accrual.execute_monthly_accrual",
        "orion_erp.orion_erp.scripts.annual_leave_accrual.execute_carry_forward"
	],
	"daily_long": [
	    "orion_erp.passport_management.tasks.send_expiry_reminders"
	],
	# "hourly": [
	# 	"orion_erp.tasks.hourly"
	# ],
	# "weekly": [
	# 	"orion_erp.tasks.weekly"
	# ],
	# "monthly": [
	# 	"orion_erp.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "orion_erp.install.before_tests"

# Overriding Methods
# ------------------------------
override_whitelisted_methods = {
	"frappe.desk.form.save.savedocs": "orion_erp.orion_erp.override.save.savedocs",
	"frappe.core.page.permission_manager.permission_manager.get_roles_and_doctypes": "orion_erp.orion_erp.override.permission_manager.get_roles_and_doctypes",
	"frappe.core.page.permission_manager.permission_manager.get_permissions": "orion_erp.orion_erp.override.permission_manager.get_permissions",
	"frappe.core.page.permission_manager.permission_manager.add": "orion_erp.orion_erp.override.permission_manager.add",
	"frappe.core.page.permission_manager.permission_manager.update": "orion_erp.orion_erp.override.permission_manager.update",
	"frappe.core.page.permission_manager.permission_manager.remove": "orion_erp.orion_erp.override.permission_manager.remove",
	"frappe.core.page.permission_manager.permission_manager.reset": "orion_erp.orion_erp.override.permission_manager.reset",
	"frappe.core.page.permission_manager.permission_manager.get_users_with_role": "orion_erp.orion_erp.override.permission_manager.get_users_with_role",
	"frappe.core.page.permission_manager.permission_manager.get_standard_permissions": "orion_erp.orion_erp.override.permission_manager.get_standard_permissions",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	"Employee": "orion_erp.orion_erp.dashboard.employee_dashboard.get_data"
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["orion_erp.utils.before_request"]
# after_request = ["orion_erp.utils.after_request"]

# Job Events
# ----------
# before_job = ["orion_erp.utils.before_job"]
# after_job = ["orion_erp.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"orion_erp.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
