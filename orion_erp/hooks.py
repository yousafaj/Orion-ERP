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
# app_include_js = "/assets/orion_erp/js/orion_erp.js"

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
    "Job Offer":"public/js/job_offer.js"
    }

# app_include_css = "/assets/orion_erp/css/listview.css"
doctype_list_js = {"Employee": "public/js/employee_list.js",}
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
        "orion_erp.orion_erp.scripts.jinja.get_qr_code"
    ],
	# "filters": "orion_erp.utils.jinja_filters
}

fixtures = [
    {
        "doctype": "Number Card",
        "filters": [
            ["name", "in", ["Total Employees"]]
        ]
    }
]

# Installation
# ------------

# before_install = "orion_erp.install.before_install"
# after_install = "orion_erp.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "orion_erp.uninstall.before_uninstall"
# after_uninstall = "orion_erp.uninstall.after_uninstall"

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
    "orion_erp.orion_erp.permission_query.leave_application.leave_application_query"
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
         "validate":"orion_erp.orion_erp.validations.leave_application.validate_leave_approval",

        "on_update":"orion_erp.orion_erp.validations.leave_application.handle_leave_approval"
    },
    "Salary Structure Assignment":{
        "validate":"orion_erp.orion_erp.validations.salary_structure_assignment.validate_ssa_employee_category"
    },
    "Additional Salary":{
        "autoname":"orion_erp.orion_erp.doctype.additional_salary.autoname",
        "validate":"orion_erp.orion_erp.doctype.additional_salary.validate",
        "on_submit":"orion_erp.orion_erp.doctype.additional_salary.on_submit",
        "on_cancel":"orion_erp.orion_erp.doctype.additional_salary.on_cancel"
    },
    "Leave Settlement": {
        "on_submit": "orion_erp.orion_erp.doctype.leave_settlement.leave_settlement.mark_ticket_paid"
    },
    "Vehicle": {
        "validate": "orion_erp.orion_erp.validations.vehicle_hooks.validate_vehicle"
    },
    "Driver": {
        "validate": "orion_erp.orion_erp.validations.driver_hooks.validate_driver"
    },
    "Customer": {
        "validate": "orion_erp.orion_erp.validations.customer_hooks.validate_customer"
    },
    "Employee": {
        "validate": ["orion_erp.orion_erp.validations.employee_hooks.validate_employee",
                    "orion_erp.orion_erp.doctype.employee.validate_allowance_amounts"],
        "after_insert": "orion_erp.orion_erp.doctype.employee.create_salary_structure_assignment",
        "on_update": "orion_erp.orion_erp.doctype.employee.create_salary_structure_assignment"
    },
    "Asset": {
        "autoname": "orion_erp.orion_erp.scripts.autoname_assets.autoname_asset"
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
            "orion_erp.orion_erp.doctype.additional_salary.create_monthly_allowances"
        ]
    },
	"daily": [
        # "orion_erp.orion_erp.doctype.employee_deduction.employee_deduction.run_deduction_cron"
		"orion_erp.tasks.daily.daily",
        "orion_erp.orion_erp.scripts.certificate_notification.certificate_expiry_notification",
        "orion_erp.orion_erp.doctype.employee.create_ticket_allowance"
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
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "orion_erp.event.get_events"
# }
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

