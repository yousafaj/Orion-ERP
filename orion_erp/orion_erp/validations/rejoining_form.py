import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, now_datetime


APPROVAL_FLOW = [
    {
        "approver_field": "custom_rejoining_approver_1",
        "status_field": "custom_status_rejoining_approver1"
    },
    {
        "approver_field": "custom_rejoining_approver_2",
        "status_field": "custom_status_rejoining_approver2"
    },
    {
        "approver_field": "custom_rejoining_approver_3",
        "status_field": "custom_status_rejoining_approver3"
    },
    {
        "approver_field": "custom_rejoining_approver_4",
        "status_field": "custom_status_rejoining_approver4"
    },
    {
        "approver_field": "custom_rejoining_approver_5",
        "status_field": "custom_status_rejoining_approver5"
    }
]


def validate_rejoining_approval(doc, method=None):
    current_user = frappe.session.user

    # Prevent direct submission if in approval flow but not fully approved
    old_doc = doc.get_doc_before_save()
    if old_doc and old_doc.docstatus == 0 and doc.docstatus == 1:
        if doc.custom_rejoining_approval_status and doc.custom_rejoining_approval_status != "Approved":
            statuses = []
            for row in APPROVAL_FLOW:
                approver = doc.get(row["approver_field"])
                status = doc.get(row["status_field"])
                if approver:
                    statuses.append(status)
            all_approved = all(s == "Approved" for s in statuses)
            if not all_approved:
                frappe.throw(
                    _("Rejoining Form cannot be submitted directly. All approvals must be completed first.")
                )

    # Validate Approved Rejoining Date equals Leave End Date
    if doc.approved_rejoining_date and doc.leave_end_date:
        if getdate(doc.approved_rejoining_date) != getdate(doc.leave_end_date):
            frappe.throw(
                _("Approved Rejoining Date must be equal to Leave End Date. Approved Rejoining Date: {0}, Leave End Date: {1}").format(
                    doc.approved_rejoining_date, doc.leave_end_date
                )
            )

    # Validate linked Leave Application
    if doc.leave_application:
        la = frappe.db.get_value(
            "Leave Application",
            doc.leave_application,
            ["employee", "docstatus"],
            as_dict=True
        )
        if not la:
            frappe.throw(_("Leave Application {0} does not exist.").format(doc.leave_application))
        if la.employee != doc.employee:
            frappe.throw(
                _("Leave Application {0} belongs to a different employee. Please select a valid Leave Application.").format(
                    doc.leave_application
                )
            )
        if la.docstatus != 1:
            frappe.throw(
                _("Leave Application {0} is not in Submitted/Approved state.").format(doc.leave_application)
            )
        duplicate = frappe.db.exists("Rejoining Form", {
            "leave_application": doc.leave_application,
            "docstatus": ["!=", 2],
            "name": ["!=", doc.name],
            "employee": doc.employee
        })
        if duplicate:
            frappe.throw(
                _("Leave Application {0} is already linked to Rejoining Form {1}.").format(
                    doc.leave_application, duplicate
                )
            )

    if current_user == "Administrator":
        return

    old_doc = doc.get_doc_before_save()

    if not old_doc:
        if not doc.custom_last_status_change:
            doc.custom_last_status_change = now_datetime()
        if not doc.custom_rejoining_approval_status:
            doc.custom_rejoining_approval_status = "Open"
        return

    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        status_field = row["status_field"]
        old_value = old_doc.get(status_field)
        new_value = doc.get(status_field)

        if old_value != new_value:
            if approver != current_user:
                frappe.throw(
                    _("You are not allowed to update {0}").format(status_field)
                )


def handle_rejoining_approval(doc, method=None):
    old_doc = doc.get_doc_before_save()
    status_changed = False

    if old_doc:
        for row in APPROVAL_FLOW:
            status_field = row["status_field"]
            if old_doc.get(status_field) != doc.get(status_field):
                status_changed = True
                break
        if status_changed:
            doc.db_set("custom_last_status_change", now_datetime())

    statuses = []
    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        status = doc.get(row["status_field"])
        if approver:
            statuses.append(status)

    if "Rejected" in statuses:
        if doc.docstatus != 0:
            frappe.db.set_value(doc.doctype, doc.name, "docstatus", 0)
        update_rejoining_status(doc)
        _notify_rejected(doc, old_doc)
        return

    if "Cancelled" in statuses:
        if doc.docstatus != 2:
            frappe.db.set_value(doc.doctype, doc.name, "docstatus", 2)
        doc.db_set("custom_last_status_change", now_datetime())
        for row in APPROVAL_FLOW:
            if doc.get(row["approver_field"]):
                doc.db_set(row["status_field"], "Cancelled")
        doc.db_set("custom_rejoining_approval_status", "Cancelled")
        _notify_cancelled(doc, old_doc)
        return

    if not statuses:
        doc.db_set("custom_rejoining_approval_status", "Open")
        return

    all_approved = all(status == "Approved" for status in statuses)

    if all_approved:
        _notify_approved(doc, old_doc)
        update_rejoining_status(doc)
        if doc.docstatus != 1:
            doc.flags.ignore_permissions = True
            frappe.flags.ignore_permissions = True
            doc.submit()
        return

    if not old_doc:
        _notify_first_approver(doc)
        update_rejoining_status(doc)
        return

    if status_changed:
        send_next_approval_email(doc)

    update_rejoining_status(doc)


def send_next_approval_email(doc):
    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return

    for index, row in enumerate(APPROVAL_FLOW):
        status_field = row["status_field"]
        old_status = old_doc.get(status_field)
        new_status = doc.get(status_field)

        if old_status != "Approved" and new_status == "Approved":
            next_index = index + 1
            next_approver = None
            while next_index < len(APPROVAL_FLOW):
                next_row = APPROVAL_FLOW[next_index]
                next_approver = doc.get(next_row["approver_field"])
                if next_approver:
                    break
                next_index += 1

            if not next_approver:
                return

            subject = "Rejoining Form Approval Notification"
            link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
            message = f"""
            <h1>Rejoining Form Notification</h1>
            <h3>Details:</h3>
            <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Employee</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Leave Type</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Status</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Open</td>
                </tr>
            </table>
            <br><br>
            <a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">Open Now</a>
            """
            try:
                frappe.sendmail(recipients=[next_approver], subject=subject, message=message, now=False)
            except Exception:
                frappe.log_error(title="Rejoining Approval Email Failed", message=f"Failed to send rejoining approval email to {next_approver}")
            return


def update_rejoining_status(doc):
    active_flow = []
    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        status = doc.get(row["status_field"])
        if approver:
            active_flow.append({"approver_field": row["approver_field"], "status": status})

    for row in active_flow:
        if row["status"] == "Rejected":
            doc.db_set("custom_rejoining_approval_status", "Rejected")
            return

    for row in active_flow:
        if row["status"] == "Cancelled":
            doc.db_set("custom_rejoining_approval_status", "Cancelled")
            return

    last_approved = None
    for row in active_flow:
        if row["status"] == "Approved":
            last_approved = row["approver_field"]
        else:
            break

    all_approved = all(row["status"] == "Approved" for row in active_flow)
    if all_approved:
        doc.db_set("custom_rejoining_approval_status", "Submit Pending")
        return

    if last_approved:
        for idx, row in enumerate(active_flow):
            if row["status"] != "Approved":
                doc.db_set("custom_rejoining_approval_status", f"Pending Approval from Approver {idx + 1}")
                return

    doc.db_set("custom_rejoining_approval_status", "Pending Approval from Approver 1")


@frappe.whitelist()
def get_employee_details(employee):
    data = frappe.get_all(
        "Employee",
        filters={"name": employee},
        fields=[
            "employee_name",
            "company",
            "department",
            "designation",
            "user_id",
            "leave_approver",
            "custom_leave_approver_1",
            "custom_leave_approver_2",
            "custom_leave_approver_3",
            "custom_leave_approver_4"
        ],
        limit=1
    )
    if data:
        return data[0]
    return {}


@frappe.whitelist()
def get_leave_application_details(leave_application):
    data = frappe.get_all(
        "Leave Application",
        filters={"name": leave_application},
        fields=[
            "employee",
            "employee_name",
            "leave_type",
            "from_date",
            "to_date",
            "total_leave_days",
            "company",
            "custom_employee_user_id"
        ],
        limit=1
    )
    if not data:
        return {}

    result = data[0]

    ld = frappe.get_all(
        "LEAVE DECLARATION",
        filters={
            "leave_application": leave_application,
            "docstatus": ["in", [1, 2]],
        },
        fields=["rejoining_date"],
        order_by="docstatus desc, creation desc",
        limit=1,
    )
    if ld and ld[0].get("rejoining_date"):
        result["tentative_rejoining_date"] = ld[0]["rejoining_date"]

    return result


def _notify_first_approver(doc):
    """Send email to the first approver when a new rejoining form is created."""
    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        if approver:
            link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
            subject = _("New Rejoining Form Approval Request - {0}").format(doc.name)
            message = f"""
            <h1>Rejoining Form Notification</h1>
            <h3>Details:</h3>
            <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Employee</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Leave Type</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Status</td>
                    <td style="padding:8px;border:1px solid #f3f3f3;">Open</td>
                </tr>
            </table>
            <br><br>
            <a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">Open Now</a>
            """
            try:
                frappe.sendmail(recipients=[approver], subject=subject, message=message, now=False)
            except Exception:
                frappe.log_error(title="Rejoining Approval Email Failed", message=f"Failed to send rejoining approval email to {approver}")
            return


def _notify_approved(doc, old_doc):
    if not old_doc:
        return
    old_statuses = [old_doc.get(row["status_field"]) for row in APPROVAL_FLOW if doc.get(row["approver_field"])]
    if all(s == "Approved" for s in old_statuses):
        return
    employee_email = doc.get("custom_employee_user_id")
    if not employee_email:
        return
    link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
    subject = _("Rejoining Form Approved - {0}").format(doc.name)
    message = f"""
    <h3>Rejoining Form Approved</h3>
    <p>Your rejoining form <b>{doc.name}</b> has been approved by all approvers.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Employee</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Approved</td></tr>
    </table>
    <br><a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Form</a>
    """
    try:
        frappe.sendmail(recipients=[employee_email], subject=subject, message=message, now=False)
    except Exception:
        frappe.log_error(title="Rejoining Approved Email Failed", message=f"Failed to send rejoining approved email to {employee_email}")


def _notify_rejected(doc, old_doc):
    if not old_doc:
        return
    was_rejected = any(old_doc.get(row["status_field"]) == "Rejected" for row in APPROVAL_FLOW if doc.get(row["approver_field"]))
    if was_rejected:
        return
    employee_email = doc.get("custom_employee_user_id")
    if not employee_email:
        return
    link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
    subject = _("Rejoining Form Rejected - {0}").format(doc.name)
    message = f"""
    <h3>Rejoining Form Rejected</h3>
    <p>Your rejoining form <b>{doc.name}</b> has been rejected.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Employee</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Rejected</td></tr>
    </table>
    <br><a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Form</a>
    """
    try:
        frappe.sendmail(recipients=[employee_email], subject=subject, message=message, now=False)
    except Exception:
        frappe.log_error(title="Rejoining Rejected Email Failed", message=f"Failed to send rejoining rejected email to {employee_email}")


def _notify_cancelled(doc, old_doc):
    if not old_doc:
        return
    was_cancelled = any(old_doc.get(row["status_field"]) == "Cancelled" for row in APPROVAL_FLOW if doc.get(row["approver_field"]))
    if was_cancelled:
        return

    recipients = set()
    employee_email = doc.get("custom_employee_user_id")
    if employee_email:
        recipients.add(employee_email)

    for row in APPROVAL_FLOW:
        approver = doc.get(row["approver_field"])
        if approver:
            recipients.add(approver)

    hr_roles = frappe.get_all("Role Details", filters={"parent": "Orion Settings", "parentfield": "default_escalation_roles"}, pluck="role")
    if hr_roles:
        hr_users = frappe.get_all("Has Role", filters={"role": ["in", hr_roles], "parenttype": "User"}, pluck="parent")
        for u in hr_users:
            recipients.add(u)

    if not recipients:
        return

    recipients = {r for r in recipients if frappe.utils.validate_email_address(r, throw=False)}
    if not recipients:
        return

    link = frappe.utils.get_url() + f"/app/rejoining-form/{doc.name}"
    subject = _("Rejoining Form Cancelled - {0}").format(doc.name)
    message = f"""
    <h3>Rejoining Form Cancelled</h3>
    <p>Rejoining form <b>{doc.name}</b> has been cancelled.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Employee</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.employee_name}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Cancelled</td></tr>
    </table>
    <br><a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Form</a>
    """
    try:
        frappe.sendmail(recipients=list(recipients), subject=subject, message=message, now=False)
    except Exception:
        frappe.log_error(title="Rejoining Cancelled Email Failed", message=f"Failed to send rejoining cancelled notification")


def on_submit_rejoining_form(doc, method=None):
	doc.db_set("custom_rejoining_approval_status", "Approved")

	_handle_linked_leave_application(doc)

	_update_asset_status_on_rejoin(doc)

	existing_la = _get_existing_leave_application(doc)

	ld_end = getdate(_get_leave_declaration_end_date(doc))
	rj_date = getdate(doc.approved_rejoining_date)

	if rj_date == ld_end:
		return

	if rj_date < ld_end:
		# Early return — cancel old LA, create new one ending on day before rejoining
		cancelled_la_name = existing_la["name"] if existing_la else None
		if existing_la:
			_cancel_leave_application(existing_la["name"])
			doc.db_set("custom_cancelled_leave_application", existing_la["name"])
		last_leave_day = add_days(rj_date, -1)
		if getdate(doc.leave_start_date) <= last_leave_day:
			new_la = _create_leave_application(doc, doc.leave_start_date, last_leave_day)
			doc.db_set("custom_created_leave_application", new_la.name)
			frappe.msgprint(
				_("Leave application {0} created from {1} to {2} due to early rejoining.").format(
					frappe.bold(new_la.name), doc.leave_start_date, last_leave_day
				),
				title=_("Leave Application Adjusted"),
				indicator="orange"
			)
		else:
			frappe.msgprint(
				_("Employee returned before leave started. Previous leave application {0} cancelled.").format(
					frappe.bold(cancelled_la_name or "N/A")
				),
				title=_("Leave Cancelled"),
				indicator="orange"
			)
		return

	if rj_date > ld_end:
		# Extended leave — create additional leave application for extra days
		ext_from = add_days(ld_end, 1)
		last_leave_day = add_days(rj_date, -1)
		if ext_from <= last_leave_day:
			ext_la = _create_leave_application(doc, ext_from, last_leave_day)
			doc.db_set("custom_created_leave_application", ext_la.name)
			frappe.msgprint(
				_("Leave application {0} created for extended leave from {1} to {2}. Kindly approve the same.").format(
					frappe.bold(ext_la.name), ext_from, last_leave_day
				),
				title=_("Extended Leave Application Created"),
				indicator="orange"
			)
		return


def _handle_linked_leave_application(doc):
    la_name = doc.get("leave_application")
    if not la_name:
        return

    if not frappe.db.exists("Leave Application", la_name):
        return

    original_la = frappe.get_doc("Leave Application", la_name)
    new_from = getdate(doc.leave_start_date)
    new_to = getdate(doc.leave_end_date)
    orig_from = getdate(original_la.from_date)
    orig_to = getdate(original_la.to_date)

    if new_from == orig_from and new_to == orig_to:
        return

    _cancel_leave_application(la_name)
    doc.db_set("custom_cancelled_leave_application", la_name)

    new_la = _create_and_submit_leave_application(doc, new_from, new_to)
    doc.db_set("custom_created_leave_application", new_la.name)

    _notify_leave_application_created(doc, new_la)

    frappe.msgprint(
        _("Leave application {0} created with updated dates {1} to {2}.").format(
            frappe.bold(new_la.name), new_from, new_to
        ),
        title=_("Leave Application Updated"),
        indicator="green"
    )


def _create_and_submit_leave_application(doc, from_date, to_date):
    la = frappe.new_doc("Leave Application")
    la.employee = doc.employee
    la.employee_name = doc.employee_name
    la.leave_type = doc.leave_type
    la.from_date = from_date
    la.to_date = to_date
    la.company = doc.company
    la.description = _("Auto-created from Rejoining Form {0}").format(doc.name)
    la.status = "Open"
    la.custom_approval_status = "Open"

    from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
    la.leave_balance = get_leave_balance_on(doc.employee, doc.leave_type, getdate(from_date))

    emp = frappe.get_cached_doc("Employee", doc.employee)
    la.leave_approver = emp.leave_approver
    la.custom_leave_approver_1 = emp.get("custom_leave_approver_1")
    la.custom_leave_approver_2 = emp.get("custom_leave_approver_2")
    la.custom_leave_approver_4 = emp.get("custom_leave_approver_3")
    la.custom_leave_approver_5 = emp.get("custom_leave_approver_4")
    la.custom_employee_user_id = emp.user_id

    la.flags.ignore_permissions = True
    la.insert()

    la.db_set("custom_sent_for_approval", 1)
    la.reload()

    for field in ("status", "custom_status_approver1", "custom_status_approver2", "custom_status_approver4", "custom_status_approver5"):
        la.db_set(field, "Approved")
    la.db_set("custom_approval_status", "Approved")

    frappe.flags.submitting_leave_from_rejoining = True
    la.submit()
    frappe.flags.submitting_leave_from_rejoining = False

    return la


def _notify_leave_application_created(doc, new_la):
    employee_email = doc.get("custom_employee_user_id")
    if not employee_email:
        return
    if not frappe.utils.validate_email_address(employee_email, throw=False):
        return

    link = frappe.utils.get_url() + f"/app/leave-application/{new_la.name}"
    subject = _("Leave Application Updated - {0}").format(new_la.name)
    message = f"""
    <h3>Leave Application Updated</h3>
    <p>Your leave application has been updated with revised dates due to your rejoining.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Application</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{new_la.name}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{new_la.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From Date</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{new_la.from_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To Date</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{new_la.to_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Approved</td></tr>
    </table>
    <br><a href="{link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Application</a>
    """
    try:
        frappe.sendmail(recipients=[employee_email], subject=subject, message=message, now=False)
    except Exception:
        frappe.log_error(title="Rejoining Leave Application Email Failed", message=f"Failed to send rejoining leave application email to {employee_email}")


def on_cancel_rejoining_form(doc, method=None):
	doc.db_set("custom_rejoining_approval_status", "Cancelled")

	_reverse_asset_status_on_cancel(doc)

	# Restore the cancelled original LA if this was an early-return case
	cancelled_la_name = doc.get("custom_cancelled_leave_application")
	if cancelled_la_name:
		try:
			restored_name = _restore_cancelled_leave_application(cancelled_la_name)
			if restored_name:
				_update_leave_declaration_reference(cancelled_la_name, restored_name)
		except Exception:
			frappe.log_error(
				title=_("Rejoining Form Cancel Error"),
				message=_("Failed to restore cancelled leave application {0} linked to Rejoining Form {1}").format(cancelled_la_name, doc.name)
			)

	# Cancel any linked leave application created from this form
	la_name = doc.get("custom_created_leave_application")
	if la_name:
		try:
			_cancel_leave_application(la_name)
		except Exception:
			frappe.log_error(
				title=_("Rejoining Form Cancel Error"),
				message=_("Failed to cancel leave application {0} linked to Rejoining Form {1}").format(la_name, doc.name)
			)


def _get_leave_declaration_end_date(doc):
    """Fetch leave_end_date from the source Leave Declaration for this employee."""
    ld = frappe.get_all(
        "LEAVE DECLARATION",
        filters={
            "employee": doc.employee,
            "leave_start_date": doc.leave_start_date,
            "docstatus": 1,
        },
        fields=["leave_end_date"],
        order_by="creation desc",
        limit=1,
    )
    if ld:
        return ld[0]["leave_end_date"]
    return doc.leave_end_date


def _get_existing_leave_application(doc):
    ld_end = _get_leave_declaration_end_date(doc)
    applications = frappe.get_all(
        "Leave Application",
        filters={
            "employee": doc.employee,
            "from_date": ["<=", ld_end],
            "to_date": [">=", doc.leave_start_date],
            "docstatus": ["!=", 2],
            "leave_type": doc.leave_type,
        },
        fields=["name", "from_date", "to_date"],
        limit=1,
    )
    return applications[0] if applications else None


def _create_leave_application(doc, from_date, to_date):
    la = frappe.new_doc("Leave Application")
    la.employee = doc.employee
    la.employee_name = doc.employee_name
    la.leave_type = doc.leave_type
    la.from_date = from_date
    la.to_date = to_date
    la.company = doc.company
    la.description = _("Auto-created from Rejoining Form {0}").format(doc.name)
    la.status = "Open"
    la.custom_approval_status = "Open"

    from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
    la.leave_balance = get_leave_balance_on(doc.employee, doc.leave_type, getdate(from_date))

    emp = frappe.get_cached_doc("Employee", doc.employee)
    la.leave_approver = emp.leave_approver
    la.custom_leave_approver_1 = emp.get("custom_leave_approver_1")
    la.custom_leave_approver_2 = emp.get("custom_leave_approver_2")
    la.custom_leave_approver_4 = emp.get("custom_leave_approver_3")
    la.custom_leave_approver_5 = emp.get("custom_leave_approver_4")
    la.custom_employee_user_id = emp.user_id

    la.flags.ignore_permissions = True
    la.insert()

    # Set balance after (total_leave_days is computed during insert by standard validate)
    la.db_set("custom_leave_balance_after", flt(la.leave_balance) - flt(la.total_leave_days))

    # Send the created leave application for approval
    from orion_erp.orion_erp.validations.leave_application import send_for_approval
    try:
        send_for_approval(la.name)
    except Exception:
        frappe.log_error(
            title=_("Leave Approval Error"),
            message=_("Failed to send leave application {0} for approval").format(la.name)
        )

    return la


def _cancel_leave_application(la_name):
    la = frappe.get_doc("Leave Application", la_name)
    if la.docstatus in (0, 1):
        la.flags.ignore_permissions = True
        la.db_set("docstatus", 2)
        la.db_set("custom_approval_status", "Cancelled")
        la.db_set("custom_leave_balance_after", 0)
        la.db_set("status", "Cancelled")
    _cancel_linked_attendance(la_name)


def _cancel_linked_attendance(la_name):
    attendance_records = frappe.get_all(
        "Attendance",
        filters={
            "leave_application": la_name,
            "docstatus": ["!=", 2]
        },
        pluck="name"
    )
    for att_name in attendance_records:
        frappe.db.set_value("Attendance", att_name, "docstatus", 2)


def _restore_cancelled_leave_application(la_name):
    """Restore a cancelled Leave Application by creating an amended copy.
    Returns the name of the restored LA, or None if no restore was needed."""
    if not frappe.db.exists("Leave Application", la_name):
        return None
    cancelled_la = frappe.get_doc("Leave Application", la_name)
    if cancelled_la.docstatus != 2:
        return None

    amended = frappe.copy_doc(cancelled_la)
    amended.amended_from = cancelled_la.name
    amended.docstatus = 0
    amended.status = "Open"
    amended.custom_approval_status = "Open"
    amended.custom_status_approver1 = "Open"
    amended.custom_status_approver2 = "Open"
    amended.custom_status_approver4 = "Open"
    amended.custom_status_approver5 = "Open"
    amended.flags.ignore_permissions = True
    amended.insert()
    return amended.name


def _update_leave_declaration_reference(old_la_name, new_la_name):
    """Update the Leave Declaration's created_leave_application to point to the restored LA."""
    ld = frappe.get_all(
        "LEAVE DECLARATION",
        filters={"created_leave_application": old_la_name, "docstatus": 1},
        fields=["name"],
        limit=1,
    )
    if ld:
        frappe.db.set_value("LEAVE DECLARATION", ld[0]["name"], "created_leave_application", new_la_name)


def reset_status_on_amend(doc, method=None):
    if not doc.amended_from:
        return
    if doc.get_doc_before_save():
        return

    for row in APPROVAL_FLOW:
        doc.set(row["status_field"], "Open")
    doc.custom_rejoining_approval_status = "Open"
    doc.custom_last_status_change = now_datetime()


@frappe.whitelist()
def cancel_draft_rejoining(docname):
	doc = frappe.get_doc("Rejoining Form", docname)

	if doc.docstatus != 0:
		frappe.throw(_("Only draft rejoining forms can be cancelled."))

	if doc.custom_rejoining_approval_status == "Cancelled":
		frappe.throw(_("Rejoining form is already cancelled."))

	for row in APPROVAL_FLOW:
		doc.db_set(row["status_field"], "Cancelled")
	doc.db_set("docstatus", 2)
	doc.db_set("custom_rejoining_approval_status", "Cancelled")

	doc.add_comment("Info", _("Rejoining form cancelled by {0}.").format(
		frappe.bold(frappe.session.user)
	))

	return True


def _get_leave_declaration_for_rejoining(doc):
	ld = frappe.get_all(
		"LEAVE DECLARATION",
		filters={
			"employee": doc.employee,
			"docstatus": 1,
			"leave_start_date": doc.leave_start_date,
		},
		fields=["name"],
		order_by="creation desc",
		limit=1,
	)
	if ld:
		return frappe.get_doc("LEAVE DECLARATION", ld[0]["name"])
	return None


def _update_asset_status_on_rejoin(doc):
	if not doc.asset_clearance_detail:
		return

	for row in doc.asset_clearance_detail:
		if not row.source_asset_handover_detail:
			continue

		previous_status = row.previous_asset_status
		if not previous_status:
			continue

		current_status = frappe.db.get_value(
			"Asset Handover Detail", row.source_asset_handover_detail, "asset_status"
		)
		if current_status == previous_status:
			continue

		update_fields = {"asset_status": previous_status}
		if previous_status == "Active":
			update_fields["return_date"] = None

		frappe.db.set_value(
			"Asset Handover Detail",
			row.source_asset_handover_detail,
			update_fields,
		)


def _reverse_asset_status_on_cancel(doc):
	if not doc.asset_clearance_detail:
		return

	for row in doc.asset_clearance_detail:
		if not row.source_asset_handover_detail:
			continue

		ld_status = row.asset_status
		if not ld_status:
			continue

		current_status = frappe.db.get_value(
			"Asset Handover Detail", row.source_asset_handover_detail, "asset_status"
		)
		if current_status == ld_status:
			continue

		update_fields = {"asset_status": ld_status}
		if ld_status in ("Returned", "Lost", "Damaged"):
			update_fields["return_date"] = row.return_date
		elif ld_status == "Active":
			update_fields["return_date"] = None

		frappe.db.set_value(
			"Asset Handover Detail",
			row.source_asset_handover_detail,
			update_fields,
		)


@frappe.whitelist()
def get_leave_declaration_assets(leave_application):
	la = frappe.db.get_value(
		"Leave Application",
		leave_application,
		["employee", "from_date"],
		as_dict=True,
	)
	if not la:
		return []

	ld = frappe.get_all(
		"LEAVE DECLARATION",
		filters={
			"employee": la.employee,
			"leave_application": leave_application,
		},
		fields=["name"],
		order_by="docstatus desc, creation desc",
		limit=1,
	)
	if ld:
		ld_doc = frappe.get_doc("LEAVE DECLARATION", ld[0]["name"])
		if ld_doc.asset_clearance_detail:
			result = []
			for row in ld_doc.asset_clearance_detail:
				result.append(_build_asset_row(row))
			return result

	assets = frappe.db.sql(
		"""
		SELECT ahd.*
		FROM `tabAsset Handover Detail` ahd
		INNER JOIN `tabAsset Handover` ah ON ah.name = ahd.parent
		WHERE ah.employee = %s
		ORDER BY ah.creation DESC
		""",
		la.employee,
		as_dict=True,
	)
	if not assets:
		return []

	result = []
	for asset in assets:
		result.append({
			"asset_type": asset.get("asset_type"),
			"asset_code": asset.get("asset_code"),
			"issued_by": asset.get("issued_by"),
			"issued_date": asset.get("issued_date"),
			"attachment_upload": asset.get("attachment_upload"),
			"asset_status": asset.get("asset_status"),
			"qty": asset.get("qty"),
			"return_date": asset.get("return_date"),
			"remarks": asset.get("remarks"),
			"sim_card_number": asset.get("sim_card_number"),
			"network": asset.get("network"),
			"sim_status": asset.get("sim_status"),
			"brand": asset.get("brand"),
			"model": asset.get("model"),
			"imei_number": asset.get("imei_number"),
			"sim_number": asset.get("sim_number"),
			"network_provider": asset.get("network_provider"),
			"condition": asset.get("condition"),
			"vehicle_type": asset.get("vehicle_type"),
			"brand_model": asset.get("brand_model"),
			"plate_number": asset.get("plate_number"),
			"vehicle_cicpa_pass": asset.get("vehicle_cicpa_pass"),
			"fuel_type": asset.get("fuel_type"),
			"mulkiya_expiry_uae_specific": asset.get("mulkiya_expiry_uae_specific"),
			"odometer_reading_at_issue": asset.get("odometer_reading_at_issue"),
			"odometer_reading_at_return": asset.get("odometer_reading_at_return"),
			"name_of_last_user": asset.get("name_of_last_user"),
			"device_type": asset.get("device_type"),
			"it_brand": asset.get("it_brand"),
			"it_model": asset.get("it_model"),
			"attachment": asset.get("attachment"),
			"card_number": asset.get("card_number"),
			"card_issue_date": asset.get("card_issue_date"),
			"lost__reissued": asset.get("lost__reissued"),
			"pass_number": asset.get("pass_number"),
			"valid_to": asset.get("valid_to"),
			"cicpa_status": asset.get("cicpa_status"),
			"linked_account": asset.get("linked_account"),
			"expiry_date": asset.get("expiry_date"),
			"request_date": asset.get("request_date"),
			"parking_status": asset.get("parking_status"),
			"parking_slot_number": asset.get("parking_slot_number"),
			"source_asset_handover": asset.get("parent"),
			"source_asset_handover_detail": asset.get("name"),
		})
	return result


def _build_asset_row(row):
	return {
		"asset_type": row.asset_type,
		"asset_code": row.asset_code,
		"issued_by": row.issued_by,
		"issued_date": row.issued_date,
		"attachment_upload": row.attachment_upload,
		"asset_status": row.asset_status,
		"qty": row.qty,
		"return_date": row.return_date,
		"remarks": row.remarks,
		"sim_card_number": row.sim_card_number,
		"network": row.network,
		"sim_status": row.sim_status,
		"brand": row.brand,
		"model": row.model,
		"imei_number": row.imei_number,
		"sim_number": row.sim_number,
		"network_provider": row.network_provider,
		"condition": row.condition,
		"vehicle_type": row.vehicle_type,
		"brand_model": row.brand_model,
		"plate_number": row.plate_number,
		"vehicle_cicpa_pass": row.vehicle_cicpa_pass,
		"fuel_type": row.fuel_type,
		"mulkiya_expiry_uae_specific": row.mulkiya_expiry_uae_specific,
		"odometer_reading_at_issue": row.odometer_reading_at_issue,
		"odometer_reading_at_return": row.odometer_reading_at_return,
		"name_of_last_user": row.name_of_last_user,
		"device_type": row.device_type,
		"it_brand": row.it_brand,
		"it_model": row.it_model,
		"attachment": row.attachment,
		"card_number": row.card_number,
		"card_issue_date": row.card_issue_date,
		"lost__reissued": row.lost__reissued,
		"pass_number": row.pass_number,
		"valid_to": row.valid_to,
		"cicpa_status": row.cicpa_status,
		"linked_account": row.linked_account,
		"expiry_date": row.expiry_date,
		"request_date": row.request_date,
		"parking_status": row.parking_status,
		"parking_slot_number": row.parking_slot_number,
		"source_asset_handover": row.source_asset_handover,
		"source_asset_handover_detail": row.source_asset_handover_detail,
		"previous_asset_status": row.previous_asset_status,
	}


@frappe.whitelist()
def update_asset_status_on_row_add(source_asset_handover_detail, previous_asset_status=None, return_date=None):
	"""Restore asset to its previous status when a row is added in Rejoining Form."""
	if not source_asset_handover_detail or not previous_asset_status:
		return

	current_status = frappe.db.get_value(
		"Asset Handover Detail", source_asset_handover_detail, "asset_status"
	)
	if current_status == previous_asset_status:
		return

	update_fields = {"asset_status": previous_asset_status}
	if previous_asset_status == "Active":
		update_fields["return_date"] = None

	frappe.db.set_value(
		"Asset Handover Detail",
		source_asset_handover_detail,
		update_fields,
	)


@frappe.whitelist()
def update_asset_status_on_row_remove(source_asset_handover_detail, asset_status=None, return_date=None):
	"""Re-apply the LD status when a row is removed in Rejoining Form."""
	if not source_asset_handover_detail or not asset_status:
		return

	current_status = frappe.db.get_value(
		"Asset Handover Detail", source_asset_handover_detail, "asset_status"
	)
	if current_status == asset_status:
		return

	update_fields = {"asset_status": asset_status}
	if asset_status in ("Returned", "Lost", "Damaged"):
		update_fields["return_date"] = return_date
	elif asset_status == "Active":
		update_fields["return_date"] = None

	frappe.db.set_value(
		"Asset Handover Detail",
		source_asset_handover_detail,
		update_fields,
	)


@frappe.whitelist()
def get_available_leave_applications(doctype, txt, searchfield, start, page_length, filters):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)

	filters = filters or {}
	employee = filters.get("employee")

	unpaid_types = frappe.get_all("Leave Type", filters={"is_lwp": 1}, pluck="name")

	query_filters = {
		"docstatus": 1,
		"custom_approval_status": "Approved",
	}
	if unpaid_types:
		query_filters["leave_type"] = ["not in", unpaid_types]
	if employee:
		query_filters["employee"] = employee
	if txt:
		query_filters["employee_name"] = ["like", f"%{txt}%"]

	apps = frappe.get_all(
		"Leave Application",
		filters=query_filters,
		fields=["name", "employee_name", "leave_type", "from_date", "to_date"],
		order_by="from_date desc",
	)
	return [
		[
			a.name,
			a.employee_name or "",
			a.leave_type or "",
			str(a.from_date) if a.from_date else "",
			str(a.to_date) if a.to_date else "",
		]
		for a in apps
	]
