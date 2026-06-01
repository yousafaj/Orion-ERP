import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, getdate

from orion_erp.passport_management.utils import get_employee_passport_info


class PassportMovement(Document):

    # ── Lifecycle hooks ───────────────────────────────────────────────────────

    def validate(self):
        self._set_defaults()
        self._sync_naming_series()
        self._populate_passport_number()
        self._validate_no_duplicate_active_in()
        self._validate_out_requires_active_in()
        self._validate_return_dates()

    def on_submit(self):
        if self.movement_type == "In":
            self.db_set("is_active_record", 1)
        elif self.movement_type == "Out":
            self._deactivate_corresponding_in_record()
            self.db_set("actual_return_date", today())

    def on_cancel(self):
        if self.movement_type == "In":
            self.db_set("is_active_record", 0)
        elif self.movement_type == "Out":
            self._reactivate_in_record()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _set_defaults(self):
        if not self.transaction_date:
            self.transaction_date = today()
        if not self.received_by:
            self.received_by = frappe.session.user

    def _populate_passport_number(self):
        """Resolve passport_number from Employee — top-level field or
        Certificates-style child table. Always re-resolves when employee is
        set so changing the linked Employee on a draft updates the value
        (the field is read-only in the UI, so there's no user input to
        protect). Leaves an existing value untouched only if the resolver
        returns nothing, so a passport_number set via API/script survives a
        re-save against an employee whose record temporarily lacks the
        passport row.
        """
        if not self.employee:
            return
        info = get_employee_passport_info(self.employee)
        resolved = info.get("passport_number")
        if resolved:
            self.passport_number = resolved

    def _sync_naming_series(self):
        """Keep naming_series aligned with movement_type — only at creation time."""
        if not self.is_new():
            return
        series_map = {"In": "PM-IN-.YYYY.-.#####", "Out": "PM-OUT-.YYYY.-.#####"}
        if self.movement_type in series_map:
            self.naming_series = series_map[self.movement_type]

    def _validate_no_duplicate_active_in(self):
        """Prevent a second active IN record for the same employee.

        Blocks both submitted-active records AND other in-flight drafts
        (docstatus 0) for the same employee — otherwise two concurrent draft
        INs could both pass validation and both set is_active_record = 1 on
        submit, defeating the constraint.
        """
        if self.movement_type != "In":
            return
        existing = frappe.db.get_value(
            "Passport Movement",
            {
                "employee": self.employee,
                "movement_type": "In",
                "docstatus": ["in", [0, 1]],
                "name": ["!=", self.name or ""],
            },
            "name",
            order_by="docstatus desc, creation asc",
        )
        if not existing:
            return
        # If existing is a submitted record, it must still be active to block
        existing_doc = frappe.db.get_value(
            "Passport Movement", existing, ["docstatus", "is_active_record"], as_dict=True
        )
        if existing_doc.docstatus == 1 and not existing_doc.is_active_record:
            return
        frappe.throw(
            _(
                "An IN record {0} already exists for {1} (draft or active). "
                "Please complete or cancel it before creating another."
            ).format(frappe.bold(existing), frappe.bold(self.employee_name)),
            title=_("Duplicate Active Record"),
        )

    def _validate_out_requires_active_in(self):
        """An OUT can only be created when an active IN record exists."""
        if self.movement_type != "Out":
            return
        active_in = frappe.db.get_value(
            "Passport Movement",
            {
                "employee": self.employee,
                "movement_type": "In",
                "is_active_record": 1,
                "docstatus": 1,
            },
            "name",
        )
        if not active_in:
            frappe.throw(
                _(
                    "No active Passport IN record found for {0}. "
                    "Cannot create an OUT movement without a prior submitted IN record."
                ).format(frappe.bold(self.employee_name)),
                title=_("Missing IN Record"),
            )

    def _validate_return_dates(self):
        if self.expected_return_date and getdate(self.expected_return_date) < getdate(
            self.transaction_date
        ):
            frappe.throw(
                _("Expected Return Date cannot be before Transaction Date."),
                title=_("Invalid Date"),
            )
        if (
            self.actual_return_date
            and self.transaction_date
            and getdate(self.actual_return_date) < getdate(self.transaction_date)
        ):
            frappe.throw(
                _("Actual Return Date cannot be before Transaction Date."),
                title=_("Invalid Date"),
            )

    def _deactivate_corresponding_in_record(self):
        """Mark the employee's active IN record as inactive when OUT is submitted."""
        active_in = frappe.db.get_value(
            "Passport Movement",
            {
                "employee": self.employee,
                "movement_type": "In",
                "is_active_record": 1,
                "docstatus": 1,
            },
            "name",
        )
        if active_in:
            frappe.db.set_value("Passport Movement", active_in, "is_active_record", 0)
            self.db_set("linked_in_record", active_in)

    def _reactivate_in_record(self):
        """When an OUT is cancelled, restore the IN record that this OUT deactivated."""
        target = self.linked_in_record
        if not target:
            # Fallback for records created before this field was added
            result = frappe.db.sql(
                """
                SELECT name FROM `tabPassport Movement`
                WHERE employee = %(employee)s
                  AND movement_type = 'In'
                  AND is_active_record = 0
                  AND docstatus = 1
                ORDER BY transaction_date DESC
                LIMIT 1
                """,
                {"employee": self.employee},
                as_dict=True,
            )
            if result:
                target = result[0].name
        if target:
            frappe.db.set_value("Passport Movement", target, "is_active_record", 1)


# ── Whitelisted API endpoints ─────────────────────────────────────────────────

@frappe.whitelist()
def get_employee_passport(employee):
    """Resolve passport_number / passport_expiry_date for an employee from
    either a top-level field or the Certificates-style child table.

    The helper uses raw SQL (it has to, because the source child table is
    discovered at runtime), which bypasses Frappe's row-level permission
    system. Enforce the Employee read permission here to keep passport
    numbers behind the same access control as the Employee record itself.
    """
    if not employee:
        return {}
    frappe.has_permission("Employee", "read", employee, throw=True)
    return get_employee_passport_info(employee)


@frappe.whitelist()
def get_active_in_record(employee):
    """Return the active IN record for an employee (used by client script)."""
    return frappe.db.get_value(
        "Passport Movement",
        {"employee": employee, "movement_type": "In", "is_active_record": 1, "docstatus": 1},
        ["name", "transaction_date", "passport_number"],
        as_dict=True,
    )


# ── Whitelisted API endpoints only — lifecycle methods are called automatically
# by Frappe via the Document class; no standalone wrappers needed here.
