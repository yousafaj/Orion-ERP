import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

COMPANY = "Orion International Facility Management LLC"
LEAVE_YEAR = ("2026-01-01", "2026-12-31")
TIER_CHILD_DOCTYPE = "Leave Pay Tier"  # create it first (README step 2)


# ------------------------------------------------------------ custom fields
def _chain(doctype, fields):
    """Give each field an insert_after, starting after the doctype's last field."""
    after = frappe.get_meta(doctype).fields[-1].fieldname
    out = []
    for f in fields:
        f = dict(f, insert_after=after)
        out.append(f)
        after = f["fieldname"]
    return out


def custom_fields():
    leave_type = [
        dict(fieldname="uae_rules_section", fieldtype="Section Break", label="UAE Leave Rules"),
        dict(fieldname="gender_restriction", fieldtype="Select", label="Gender Restriction", options="Any\nMale\nFemale", default="Any"),
        dict(fieldname="religion_restriction", fieldtype="Data", label="Religion Restriction"),
        dict(fieldname="one_time_only", fieldtype="Check", label="One-Time Only (once per employment)"),
        dict(fieldname="min_days_per_application", fieldtype="Float", label="Minimum Days Per Application"),
        dict(fieldname="uae_rules_col", fieldtype="Column Break"),
        dict(fieldname="custom_requires_event_dateel="Requires Event Date"),
        dict(fieldname="event_allow_before_days", fieldtype="Int", label="Leave May Start This Many Days Before Event", depends_on="custom_requires_event_date
        dict(fieldname="event_window_months", fieldtype="Int", label="Leave Must Start Within (Months) of Event", depends_on="custom_requires_event_date
        dict(fieldname="document_mode", fieldtype="Select", label="Supporting Document", options="None\nUpload later\nMandatory", default="None"),
        dict(fieldname="document_deadline_days", fieldtype="Int", label="Document Deadline (Days From Leave Start)", depends_on="eval:doc.document_mode=='Upload later'"),
        dict(fieldname="pay_tiers_section", fieldtype="Section Break", label="Pay Tiers (cumulative days per leave year)"),
        dict(fieldname="pay_tiers", fieldtype="Table", label="Pay Tiers", options=TIER_CHILD_DOCTYPE),
    ]
    leave_application = [
        dict(fieldname="uae_section", fieldtype="Section Break", label="UAE Leave Details"),
        dict(fieldname="custom_requires_event_dateel="Requires Event Date", fetch_from="leave_type.custom_requires_event_date,
        dict(fieldname="document_mode", fieldtype="Data", label="Document Mode", fetch_from="leave_type.document_mode", hidden=1, read_only=1),
        dict(fieldname="event_date", fieldtype="Date", label="Event Date (birth / death / expected delivery)", depends_on="custom_requires_event_date
        dict(fieldname="supporting_document", fieldtype="Attach", label="Supporting Document", depends_on="eval:doc.document_mode!='None'"),
        dict(fieldname="uae_col", fieldtype="Column Break"),
        dict(fieldname="full_pay_days", fieldtype="Float", label="Full Pay Days", read_only=1),
        dict(fieldname="half_pay_days", fieldtype="Float", label="Half Pay Days", read_only=1),
        dict(fieldname="unpaid_days", fieldtype="Float", label="Unpaid Days", read_only=1,
             description="Estimate when saved. Payroll always recalculates from approved leave."),
    ]
    fields = {"Leave Type": _chain("Leave Type", leave_type),
              "Leave Application": _chain("Leave Application", leave_application)}
    if not frappe.get_meta("Employee").has_field("religion"):
        fields["Employee"] = _chain("Employee", [dict(fieldname="religion", fieldtype="Data", label="Religion")])
    return fields


# -------------------------------------------------------- salary components
SALARY_COMPONENTS = [
    ("Sick Leave Deduction - Half Pay", "SLDH", "Deduction"),
    ("Sick Leave Deduction - Unpaid", "SLDU", "Deduction"),
    ("Maternity Leave Deduction - Half Pay", "MLDH", "Deduction"),
    ("Maternity Leave Deduction - Unpaid", "MLDU", "Deduction"),
    ("Leave Encashment", "LENC", "Earning"),
]


def create_salary_components():
    for name, abbr, typ in SALARY_COMPONENTS:
        if not frappe.db.exists("Salary Component", name):
            frappe.get_doc({"doctype": "Salary Component", "salary_component": name,
                            "salary_component_abbr": abbr, "type": typ}).insert()
            print("Salary Component created:", name)


# --------------------------------------------------------------- leave types
SICK_TIERS = [(15, 100), (45, 50), (90, 0)]
MATERNITY_TIERS = [(45, 100), (60, 50), (105, 0)]

LEAVE_TYPES = [
    dict(leave_type_name="Annual Leave", max_leaves_allowed=30, is_earned_leave=1, earned_leave_frequency="Monthly",
         allocate_on_day="Last Day", rounding="0.5", is_carry_forward=1, maximum_carry_forwarded_leaves=15,  # 15 = 50%, pending HR
         allow_encashment=1, earning_component="Leave Encashment"),
    dict(leave_type_name="Sick Leave", max_leaves_allowed=90, applicable_after=180,
         document_mode="Upload later", document_deadline_days=3, tiers=SICK_TIERS),
    dict(leave_type_name="Maternity Leave", max_leaves_allowed=105, gender_restriction="Female",
         document_mode="Mandatory", custom_requires_event_dateys=30, tiers=MATERNITY_TIERS),
    dict(leave_type_name="Paternity Leave", max_leaves_allowed=5, max_continuous_days_allowed=5,
         gender_restriction="Male",  # UAE page says parental leave for both parents: confirm with HR
         document_mode="Upload later", document_deadline_days=30, custom_requires_event_date),
    dict(leave_type_name="Bereavement Leave - Spouse", max_leaves_allowed=5, max_continuous_days_allowed=5,
         document_mode="Upload later", document_deadline_days=5, custom_requires_event_date
    dict(leave_type_name="Bereavement Leave - Close Family", max_leaves_allowed=3, max_continuous_days_allowed=3,
         document_mode="Upload later", document_deadline_days=5, custom_requires_event_date
    dict(leave_type_name="Hajj and Umrah Leave", is_lwp=1, max_continuous_days_allowed=30,
         min_days_per_application=15,  # 15-day minimum is company policy, not law
         one_time_only=1, religion_restriction="Muslim", document_mode="Mandatory"),
    dict(leave_type_name="Emergency Leave", is_lwp=1, max_continuous_days_allowed=15,
         document_mode="Upload later", document_deadline_days=3),
    dict(leave_type_name="Leave Without Pay", is_lwp=1),
]


def create_leave_types():
    meta = frappe.get_meta("Leave Type")
    for spec in LEAVE_TYPES:
        spec = dict(spec)
        name = spec["leave_type_name"]
        if frappe.db.exists("Leave Type", name):
            print("Leave Type exists, skipped:", name)
            continue
        tiers = spec.pop("tiers", [])
        values, skipped = {"doctype": "Leave Type"}, []
        for k, v in spec.items():
            (values.__setitem__(k, v) if meta.has_field(k) else skipped.append(k))
        values["pay_tiers"] = [{"up_to_day": u, "pay_percent": p} for u, p in tiers]
        frappe.get_doc(values).insert()
        print("Leave Type created:", name, ("(fields not in this version: %s)" % ", ".join(skipped)) if skipped else "")
    if frappe.db.exists("Leave Type", "Casual Leave"):
        print("WARNING: 'Casual Leave' exists. Delete it (or disable it) - it is not a UAE leave type.")


# ------------------------------------------------- leave period & policies
POLICIES = {
    "UAE Policy - Male": [("Annual Leave", 30), ("Sick Leave", 90), ("Paternity Leave", 5),
                          ("Bereavement Leave - Spouse", 5), ("Bereavement Leave - Close Family", 3)],
    "UAE Policy - Female": [("Annual Leave", 30), ("Sick Leave", 90), ("Maternity Leave", 105),
                            ("Bereavement Leave - Spouse", 5), ("Bereavement Leave - Close Family", 3)],
}


def create_leave_period():
    if frappe.db.exists("Leave Period", {"company": COMPANY, "from_date": LEAVE_YEAR[0]}):
        return
    frappe.get_doc({"doctype": "Leave Period", "from_date": LEAVE_YEAR[0], "to_date": LEAVE_YEAR[1],
                    "is_active": 1, "company": COMPANY}).insert()
    print("Leave Period created")


def create_leave_policies():
    for title, rows in POLICIES.items():
        if frappe.db.exists("Leave Policy", {"title": title}):
            continue
        doc = frappe.get_doc({"doctype": "Leave Policy", "title": title,
                              "leave_policy_details": [{"leave_type": lt, "annual_allocation": d} for lt, d in rows]})
        doc.insert()
        doc.submit()
        print("Leave Policy created:", title)


def run():
    if not frappe.db.exists("DocType", TIER_CHILD_DOCTYPE):
        frappe.throw(f"Create the child DocType '{TIER_CHILD_DOCTYPE}' first (README step 2).")
    create_custom_fields(custom_fields(), update=True)
    create_salary_components()
    create_leave_types()
    create_leave_period()
    create_leave_policies()
    frappe.db.commit()
    print("Done.")


def assign_policies():
    """Give every active employee the Male/Female policy for the leave period."""
    period = frappe.db.get_value("Leave Period", {"company": COMPANY, "from_date": LEAVE_YEAR[0]}, "name")
    policy = {g: frappe.db.get_value("Leave Policy", {"title": t, "docstatus": 1}, "name")
              for g, t in (("Female", "UAE Policy - Female"), ("Male", "UAE Policy - Male"))}
    for emp in frappe.get_all("Employee", filters={"status": "Active", "company": COMPANY}, fields=["name", "gender"]):
        if frappe.db.exists("Leave Policy Assignment", {"employee": emp.name, "leave_period": period, "docstatus": 1}):
            continue
        try:
            doc = frappe.get_doc({"doctype": "Leave Policy Assignment", "employee": emp.name,
                                  "leave_policy": policy["Female" if emp.gender == "Female" else "Male"],
                                  "assignment_based_on": "Leave Period", "leave_period": period})
            doc.insert()
            doc.submit()
        except Exception:
            frappe.log_error(title=f"Leave policy assignment failed: {emp.name}", message=frappe.get_traceback())
            print("FAILED:", emp.name, "(see Error Log)")
    frappe.db.commit()
