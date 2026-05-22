app_name = "rental_management"
app_title = "Rental Management"
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
# 		"name": "rental_management",
# 		"logo": "/assets/rental_management/logo.png",
# 		"title": "Rental Management",
# 		"route": "/rental_management",
# 		"has_permission": "rental_management.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/rental_management/css/rental_management.css"
# app_include_js = "/assets/rental_management/js/rental_management.js"

# include js, css files in header of web template
# web_include_css = "/assets/rental_management/css/rental_management.css"
# web_include_js = "/assets/rental_management/js/rental_management.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "rental_management/public/scss/website"

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
    "Driver": "public/js/driver.js"
    }

# app_include_css = "/assets/rental_management/css/listview.css"
doctype_list_js = {"Employee": "public/js/employee_list.js",}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "rental_management/public/icons.svg"

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
# 	"methods": "rental_management.utils.jinja_methods",
# 	"filters": "rental_management.utils.jinja_filters"
# }

jinja = {
	"methods": [
        "rental_management.rental_management.scripts.jinja.get_qr_code"
    ],
	# "filters": "rental_management.utils.jinja_filters
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
    }
]

# Installation
# ------------

# before_install = "rental_management.install.before_install"
# after_install = "rental_management.install.after_install"

after_install = "rental_management.passport_management.install.after_install"
after_migrate = "rental_management.passport_management.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "rental_management.uninstall.before_uninstall"
# after_uninstall = "rental_management.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "rental_management.utils.before_app_install"
# after_app_install = "rental_management.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "rental_management.utils.before_app_uninstall"
# after_app_uninstall = "rental_management.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "rental_management.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways
permission_query_conditions = {
    "Additional Salary": "rental_management.rental_management.permission_query.additonal_salary.get_additional_salary_permission_query",
	"Salary Structure Assignment": "rental_management.rental_management.permission_query.salary_structure_assignment.get_ssa_permission_query",
    "Leave Application":
    "rental_management.rental_management.permission_query.leave_application.leave_application_query"
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
         "validate":"rental_management.rental_management.validations.leave_application.validate_leave_approval",

        "on_update":"rental_management.rental_management.validations.leave_application.handle_leave_approval"
    },
    "Salary Structure Assignment":{
        "validate":"rental_management.rental_management.validations.salary_structure_assignment.validate_ssa_employee_category"
    },
    "Additional Salary":{
        "autoname":"rental_management.rental_management.doctype.additional_salary.autoname",
        "validate":"rental_management.rental_management.doctype.additional_salary.validate",
        "on_submit":"rental_management.rental_management.doctype.additional_salary.on_submit",
        "on_cancel":"rental_management.rental_management.doctype.additional_salary.on_cancel"
    },
    "Leave Settlement": {
        "on_submit": "rental_management.rental_management.doctype.leave_settlement.leave_settlement.mark_ticket_paid"
    },
    "Vehicle": {
        "validate": "rental_management.rental_management.validations.vehicle_hooks.validate_vehicle"
    },
    "Driver": {
        "validate": "rental_management.rental_management.validations.driver_hooks.validate_driver",
        "after_insert": "rental_management.rental_management.validations.driver_hooks.after_insert_driver"
    },
    "Customer": {
        "validate": "rental_management.rental_management.validations.customer_hooks.validate_customer"
    },
    "Employee": {
        "validate": ["rental_management.rental_management.validations.employee_hooks.validate_employee",
                    "rental_management.rental_management.doctype.employee.validate_allowance_amounts"],
        "after_insert": "rental_management.rental_management.doctype.employee.create_salary_structure_assignment",
        "on_update": "rental_management.rental_management.doctype.employee.create_salary_structure_assignment"
    },
    "Asset": {
        "autoname": "rental_management.rental_management.scripts.autoname_assets.autoname_asset"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"rental_management.tasks.all"
	# ],
    "cron": {
        "0 6 30 * *": [
            "rental_management.rental_management.doctype.additional_salary.create_monthly_allowances"
        ]
    },
	"daily": [
        # "rental_management.rental_management.doctype.employee_deduction.employee_deduction.run_deduction_cron"
		"rental_management.tasks.daily.daily",
        "rental_management.rental_management.scripts.certificate_notification.certificate_expiry_notification",
        "rental_management.rental_management.doctype.employee.create_ticket_allowance",
        "rental_management.passport_management.tasks.send_overdue_passport_alerts",
        "rental_management.rental_management.doctype.cicpa.cicpa.auto_expire_cicpas",
        "rental_management.rental_management.doctype.loa.loa.auto_expire_loas"
	],
	"daily_long": [
	    "rental_management.passport_management.tasks.send_expiry_reminders"
	],
	# "hourly": [
	# 	"rental_management.tasks.hourly"
	# ],
	# "weekly": [
	# 	"rental_management.tasks.weekly"
	# ],
	# "monthly": [
	# 	"rental_management.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "rental_management.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "rental_management.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	"Employee": "rental_management.rental_management.dashboard.employee_dashboard.get_data"
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["rental_management.utils.before_request"]
# after_request = ["rental_management.utils.after_request"]

# Job Events
# ----------
# before_job = ["rental_management.utils.before_job"]
# after_job = ["rental_management.utils.after_job"]

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
# 	"rental_management.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

