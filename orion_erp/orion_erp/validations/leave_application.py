import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, add_days


APPROVAL_FLOW = [

    {
        "approver_field": "leave_approver",
        "status_field": "status"
    },

    {
        "approver_field": "custom_leave_approver_1",
        "status_field": "custom_status_approver1"
    },

    {
        "approver_field": "custom_leave_approver_2",
        "status_field": "custom_status_approver2"
    },

    {
        "approver_field": "custom_leave_approver_4",
        "status_field": "custom_status_approver4"
    },

    {
        "approver_field": "custom_leave_approver_5",
        "status_field": "custom_status_approver5"
    }
]

# =========================================================
# VALIDATION
# =========================================================

def validate_leave_approval(doc, method=None):

    current_user = frappe.session.user

    if current_user == "Administrator":
        return

    old_doc = doc.get_doc_before_save()

    if not old_doc:
        if not doc.custom_last_status_change:
            doc.custom_last_status_change = now_datetime()
        if not doc.custom_approval_status:
            doc.custom_approval_status = "Open"
        return

    for row in APPROVAL_FLOW:

        approver = doc.get(
            row["approver_field"]
        )

        status_field = row["status_field"]

        old_value = old_doc.get(status_field)

        new_value = doc.get(status_field)

        # Status changed
        if old_value != new_value:

            # Only approver can update
            if approver != current_user:

                frappe.throw(
                    _("You are not allowed to update {0}")
                    .format(status_field)
                )



# =========================================================
# HANDLE APPROVAL
# =========================================================
def handle_leave_approval(doc, method=None):

    old_doc = doc.get_doc_before_save()
    status_changed = False

    # Track status changes for auto-escalation
    if old_doc:
        for row in APPROVAL_FLOW:
            status_field = row["status_field"]
            if old_doc.get(status_field) != doc.get(status_field):
                status_changed = True
                break
        if status_changed:
            doc.db_set("custom_last_status_change", now_datetime())
            doc.db_set("custom_reminder_sent", 0)
            doc.db_set("custom_escalation_sent", 0)

    statuses = []

    for row in APPROVAL_FLOW:

        approver = doc.get(
            row["approver_field"]
        )

        status = doc.get(
            row["status_field"]
        )

        # Only active approvers
        if approver:

            statuses.append(status)

    
    # REJECTED
    if "Rejected" in statuses:

        if doc.docstatus != 0:

            frappe.db.set_value(
                doc.doctype,
                doc.name,
                "docstatus",
                0
            )

        _notify_rejected(doc, old_doc)
        return

    
    # CANCELLED
    if "Cancelled" in statuses:

        if doc.docstatus != 2:

            frappe.db.set_value(
                doc.doctype,
                doc.name,
                "docstatus",
                2
            )

        doc.db_set("custom_last_status_change", now_datetime())
        doc.db_set("custom_reminder_sent", 0)

        for row in APPROVAL_FLOW:
            if doc.get(row["approver_field"]):
                doc.db_set(row["status_field"], "Cancelled")

        doc.db_set("custom_approval_status", "Cancelled")

        _notify_cancelled(doc, old_doc)
        return

    # ALL APPROVED
    all_approved = all(
        status == "Approved"
        for status in statuses
    )

    if all_approved:

        _notify_approved(doc, old_doc)
        update_leave_application_status(doc)

        if doc.docstatus != 1:
            frappe.msgprint(
                _("All approvers have approved. Please submit the document.")
            )

        return

    if status_changed:
        send_next_approval_email(doc)

    update_leave_application_status(doc)

# NEXT APPROVER EMAIL
def send_next_approval_email(doc):

    old_doc = doc.get_doc_before_save()

    if not old_doc:
        return

    for index, row in enumerate(APPROVAL_FLOW):

        status_field = row["status_field"]

        old_status = old_doc.get(status_field)

        new_status = doc.get(status_field)

        # ONLY WHEN STATUS CHANGED TO APPROVED
        if (
            old_status != "Approved"
            and new_status == "Approved"
        ):

            next_index = index + 1

            if next_index >= len(APPROVAL_FLOW):
                return

            next_row = APPROVAL_FLOW[next_index]

            next_approver = doc.get(
                next_row["approver_field"]
            )

            if not next_approver:
                return

            subject = "Leave Approval Notification"

            leave_link = (
                frappe.utils.get_url()
                + f"/app/leave-application/{doc.name}"
            )

            message = f"""
            <h1>Leave Application Notification</h1>

            <h3>Details:</h3>

            <table class="table table-bordered small"
                style="
                    width:100%;
                    border-collapse:collapse;
                    border:1px solid #f3f3f3;
                    max-width:500px
                ">

                <tr>
                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        Employee
                    </td>

                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        {doc.employee_name}
                    </td>
                </tr>

                <tr>
                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        Leave Type
                    </td>

                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        {doc.leave_type}
                    </td>
                </tr>

                <tr>
                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        From Date
                    </td>

                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        {doc.from_date}
                    </td>
                </tr>

                <tr>
                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        To Date
                    </td>

                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        {doc.to_date}
                    </td>
                </tr>

                <tr>
                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        Status
                    </td>

                    <td style="padding:8px; border:1px solid #f3f3f3;">
                        Open
                    </td>
                </tr>

            </table>

            <br><br>

            <a
                href="{leave_link}"
                target="_blank"
                style="
                    color:#fff;
                    text-decoration:none;
                    padding:4px 20px;
                    font-size:13px;
                    border-radius:6px;
                    background-color:#171717;
                    display:inline-block;
                    line-height:20px;
                "
            >
                Open Now
            </a>
            """

            frappe.sendmail(

                recipients=[next_approver],

                subject=subject,

                message=message,

                now=False
            )

            return
        

@frappe.whitelist()
def get_employee_details(employee):

    data = frappe.get_all(

        "Employee",

        filters={
            "name": employee
        },

        fields=[

            "employee_name",

            "company",

            "department",

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


def validate_annual_leave_avail(doc, method=None):
    if doc.leave_type != "Annual Leave" or doc.docstatus == 1:
        return

    employee_doj = frappe.db.get_value("Employee", doc.employee, "date_of_joining")
    if not employee_doj:
        return

    doj = getdate(employee_doj)
    today = getdate()

    if doj > today:
        frappe.throw(_("Employee has not yet joined."))

    completed_months = get_completed_months(doj, today)

    balance = frappe.db.sql("""
        SELECT COALESCE(SUM(leaves), 0)
        FROM `tabLeave Ledger Entry`
        WHERE employee = %s
          AND leave_type = 'Annual Leave'
          AND docstatus = 1
          AND is_expired = 0
    """, doc.employee)[0][0] or 0

    balance = flt(balance)

    if completed_months < 12 and doc.total_leave_days > balance:
        frappe.throw(
            _(
                "You have not completed 1 year of service yet. "
                "Annual Leave avail is restricted to your accrued balance of {0} days."
            ).format(balance)
        )


def get_completed_months(doj, ref_date):
    months = (ref_date.year - doj.year) * 12 + (ref_date.month - doj.month)
    if ref_date.day < doj.day:
        months -= 1
    return max(0, months)


def validate_medical_certificate(doc, method=None):
    if not doc.leave_type:
        return

    leave_type = frappe.db.get_value(
        "Leave Type",
        doc.leave_type,
        [
            "custom_medical_certificate_required",
            "custom_medical_certificate_required_by"
        ],
        as_dict=True
    )

    if not leave_type or not leave_type.custom_medical_certificate_required:
        doc.custom_medical_certificate_status = ""
        return

    if doc.custom_medical_certificate:
        doc.custom_medical_certificate_status = "Submitted"
        return

    # For List View / Reports
    doc.custom_medical_certificate_status = "Pending"

    hrs_text = ""
    if leave_type.custom_medical_certificate_required_by:
        hrs_text = _(
            " The certificate should be submitted within {0} hours."
        ).format(leave_type.custom_medical_certificate_required_by)

    frappe.msgprint(
        title=_("Medical Certificate Required"),
        indicator="orange",
        msg=_(
            "A medical certificate is required for the selected leave type and has not yet been attached."
        ) + hrs_text
    )

def validate_paternity_leave(doc, method=None):
    if doc.leave_type != "Paid Paternity Leave":
        return

    if not doc.custom_child_date_of_birth:
        frappe.throw(
            _("Child's Date of Birth is required for Paid Paternity Leave.")
        )

    child_dob = getdate(doc.custom_child_date_of_birth)
    six_months_later = add_days(child_dob, 183)

    if doc.from_date and getdate(doc.from_date) > six_months_later:
        frappe.throw(
            _("Paid Paternity Leave must be taken within 6 months of the child's date of birth. From Date ({0}) exceeds the 6-month period from child's date of birth ({1}).").format(
                frappe.bold(str(doc.from_date)),
                frappe.bold(str(doc.custom_child_date_of_birth))
            )
        )

    if doc.to_date and getdate(doc.to_date) > six_months_later:
        frappe.throw(
            _("Paid Paternity Leave must be taken within 6 months of the child's date of birth. To Date ({0}) exceeds the 6-month period from child's date of birth ({1}).").format(
                frappe.bold(str(doc.to_date)),
                frappe.bold(str(doc.custom_child_date_of_birth))
            )
        )


def validate_hajj_umrah_leave(doc, method=None):
    if doc.leave_type != "HAJI/ UMRAH LEAVE":
        return

    religion = frappe.db.get_value("Employee", doc.employee, "custom_religion")
    if religion != "Muslim":
        frappe.throw(
            _("Hajj/Umrah Leave is only applicable to Muslim employees."),
            title=_("Ineligible")
        )

    max_days = frappe.db.get_value("Leave Type", doc.leave_type, "max_leaves_allowed") or 0
    if max_days and doc.total_leave_days > max_days:
        frappe.throw(
            _("Hajj/Umrah Leave cannot exceed {0} days as per the Leave Type configuration. You have requested {1} days.").format(
                frappe.bold(str(max_days)),
                frappe.bold(str(doc.total_leave_days))
            ),
            title=_("Exceeds Maximum Leave Days")
        )

    existing = frappe.db.exists("Leave Application", {
        "employee": doc.employee,
        "leave_type": doc.leave_type,
        "docstatus": 1,
        "status": "Approved",
        "name": ["!=", doc.name]
    })

    if existing:
        frappe.throw(
            _("Employee has already availed Hajj/Umrah Leave. This leave type can only be availed once during the entire employment period."),
            title=_("Already Availed")
        )


def reset_status_on_amend(doc, method=None):
    if not doc.amended_from:
        return

    if doc.get_doc_before_save():
        return

    doc.status = "Open"
    doc.custom_status_approver1 = "Open"
    doc.custom_status_approver2 = "Open"
    doc.custom_status_approver4 = "Open"
    doc.custom_status_approver5 = "Open"
    doc.custom_approval_status = "Open"
    doc.custom_last_status_change = now_datetime()
    doc.custom_reminder_sent = 0
    doc.custom_escalation_sent = 0


def update_leave_application_status(doc):

    active_flow = []

    for row in APPROVAL_FLOW:

        approver = doc.get(row["approver_field"])
        status = doc.get(row["status_field"])

        if approver:

            active_flow.append({
                "approver_field": row["approver_field"],
                "status": status
            })

    # =====================================================
    # REJECTED
    # =====================================================

    for row in active_flow:

        if row["status"] == "Rejected":

            doc.db_set(
                "custom_approval_status",
                "Rejected"
            )

            return

    # =====================================================
    # CANCELLED
    # =====================================================

    for row in active_flow:

        if row["status"] == "Cancelled":

            doc.db_set(
                "custom_approval_status",
                "Cancelled"
            )

            return

    approval_labels = {

        "leave_approver":
        "Pending Approval from Approver 2",

        "custom_leave_approver_1":
        "Pending Approval from Approver 3",

        "custom_leave_approver_2":
        "Pending Approval from Approver 4",

        "custom_leave_approver_4":
        "Pending Approval from Approver 5",

        "custom_leave_approver_5":
        "Pending Approval from Approver 6"
    }

    last_approved = None

    for row in active_flow:

        if row["status"] == "Approved":

            last_approved = row["approver_field"]

        else:
            break

    # =====================================================
    # FULLY APPROVED
    # =====================================================

    all_approved = all(
        row["status"] == "Approved"
        for row in active_flow
    )

    if all_approved:

        doc.db_set(
            "custom_approval_status",
            "Submit Pending"
        )

        return

    # =====================================================
    # PARTIAL APPROVAL
    # =====================================================

    if last_approved:

        doc.db_set(
            "custom_approval_status",
            approval_labels.get(last_approved)
        )

        return

    # =====================================================
    # DEFAULT
    # =====================================================

    doc.db_set(
        "custom_approval_status",
        "Pending Approval from Approver 1"
    )


# =========================================================
# NOTIFICATION HELPERS
# =========================================================

def _notify_approved(doc, old_doc):
    if not old_doc:
        return
    old_statuses = [old_doc.get(row["status_field"]) for row in APPROVAL_FLOW if doc.get(row["approver_field"])]
    if all(s == "Approved" for s in old_statuses):
        return
    employee_email = doc.get("custom_employee_user_id")
    if not employee_email:
        return
    leave_link = frappe.utils.get_url() + f"/app/leave-application/{doc.name}"
    subject = _("Leave Application Approved - {0}").format(doc.name)
    message = f"""
    <h3>Leave Application Approved</h3>
    <p>Your leave application <b>{doc.name}</b> has been approved by all approvers.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.from_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.to_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Approved</td></tr>
    </table>
    <br><a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Application</a>
    """
    frappe.sendmail(recipients=[employee_email], subject=subject, message=message, now=False)


def _notify_rejected(doc, old_doc):
    if not old_doc:
        return
    was_rejected = any(old_doc.get(row["status_field"]) == "Rejected" for row in APPROVAL_FLOW if doc.get(row["approver_field"]))
    if was_rejected:
        return
    employee_email = doc.get("custom_employee_user_id")
    if not employee_email:
        return
    leave_link = frappe.utils.get_url() + f"/app/leave-application/{doc.name}"
    subject = _("Leave Application Rejected - {0}").format(doc.name)
    message = f"""
    <h3>Leave Application Rejected</h3>
    <p>Your leave application <b>{doc.name}</b> has been rejected.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.from_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.to_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Rejected</td></tr>
    </table>
    <br><a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Application</a>
    """
    frappe.sendmail(recipients=[employee_email], subject=subject, message=message, now=False)


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

    hr_user = frappe.db.get_single_value("Orion Settings", "default_escalation_user")
    if hr_user:
        recipients.add(hr_user)

    if not recipients:
        return

    leave_link = frappe.utils.get_url() + f"/app/leave-application/{doc.name}"
    subject = _("Leave Application Cancelled - {0}").format(doc.name)
    message = f"""
    <h3>Leave Application Cancelled</h3>
    <p>Leave application <b>{doc.name}</b> has been cancelled.</p>
    <table class="table table-bordered small" style="width:100%;border-collapse:collapse;border:1px solid #f3f3f3;max-width:500px;">
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Leave Type</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.leave_type}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>From</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.from_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>To</b></td><td style="padding:8px;border:1px solid #f3f3f3;">{doc.to_date}</td></tr>
        <tr><td style="padding:8px;border:1px solid #f3f3f3;"><b>Status</b></td><td style="padding:8px;border:1px solid #f3f3f3;">Cancelled</td></tr>
    </table>
    <br><a href="{leave_link}" target="_blank" style="color:#fff;text-decoration:none;padding:4px 20px;font-size:13px;border-radius:6px;background-color:#171717;display:inline-block;line-height:20px;">View Application</a>
    """
    frappe.sendmail(recipients=list(recipients), subject=subject, message=message, now=False)


# =========================================================
# ON SUBMIT
# =========================================================
def on_submit_leave_application(doc, method=None):

    doc.db_set(
        "custom_approval_status",
        "Approved"
    )


def on_cancel_leave_application(doc, method=None):

    doc.db_set(
        "custom_approval_status",
        "Cancelled"
    )


# =========================================================
# CANCEL DRAFT LEAVE APPLICATION
# =========================================================

@frappe.whitelist()
def cancel_draft_leave(docname):
    doc = frappe.get_doc("Leave Application", docname)

    if doc.docstatus != 0:
        frappe.throw(_("Only draft leave applications can be cancelled."))

    if doc.status == "Cancelled":
        frappe.throw(_("Leave application is already cancelled."))

    from frappe.utils import getdate
    if getdate(doc.from_date) <= getdate():
        frappe.throw(_("Leave cannot be cancelled after the start date has passed."))

    doc.db_set("status", "Cancelled")
    doc.db_set("custom_status_approver1", "Cancelled")
    doc.db_set("custom_status_approver2", "Cancelled")
    doc.db_set("custom_status_approver4", "Cancelled")
    doc.db_set("custom_status_approver5", "Cancelled")
    doc.db_set("docstatus", 2)
    doc.db_set("custom_approval_status", "Cancelled")

    doc.add_comment(
        "Info",
        _("Leave application cancelled by {0} before start date.").format(
            frappe.bold(frappe.session.user)
        )
    )

    return True


# =========================================================
# LEAVE TYPE FILTER
# < 6 months → Orion Settings allowed types (ignore allocations)
# >= 6 months → only allocated leave types
# =========================================================

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_leave_types_for_employee(doctype, txt, searchfield, start, page_len, filters):
    employee = filters.get("employee") if filters else None
    if not employee:
        return frappe.db.sql("""
            SELECT name FROM `tabLeave Type`
            WHERE name LIKE %(txt)s
            LIMIT %(start)s, %(page_len)s
        """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

    doj = frappe.db.get_value("Employee", employee, "date_of_joining")
    if not doj:
        return frappe.db.sql("""
            SELECT name FROM `tabLeave Type`
            WHERE name LIKE %(txt)s
            LIMIT %(start)s, %(page_len)s
        """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

    completed_months = get_completed_months(getdate(doj), getdate())

    # Employee within 6 months → show only Orion Settings allowed types
    if completed_months < 6:
        allowed_types = frappe.get_all(
            "Leave Type Details",
            filters={"parent": "Orion Settings", "parentfield": "leave_types_within_six_months"},
            pluck="leave_type"
        )

        if not allowed_types:
            return frappe.db.sql("""
                SELECT name FROM `tabLeave Type`
                WHERE name LIKE %(txt)s
                LIMIT %(start)s, %(page_len)s
            """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

        return frappe.db.sql("""
            SELECT name FROM `tabLeave Type`
            WHERE name IN %(allowed_types)s
              AND name LIKE %(txt)s
            LIMIT %(start)s, %(page_len)s
        """, {"allowed_types": allowed_types, "txt": f"%{txt}%", "start": start, "page_len": page_len})

    # Employee 6+ months → show only allocated leave types
    allocated_types = frappe.db.sql("""
        SELECT DISTINCT leave_type
        FROM `tabLeave Allocation`
        WHERE employee = %(employee)s
          AND docstatus = 1
          AND expired = 0
          AND CURDATE() BETWEEN from_date AND to_date
    """, {"employee": employee}, pluck="leave_type")

    if not allocated_types:
        return []

    return frappe.db.sql("""
        SELECT name FROM `tabLeave Type`
        WHERE name IN %(allocated_types)s
          AND name LIKE %(txt)s
        LIMIT %(start)s, %(page_len)s
    """, {"allocated_types": allocated_types, "txt": f"%{txt}%", "start": start, "page_len": page_len})