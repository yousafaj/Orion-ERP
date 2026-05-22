import frappe


def execute():
    """Sync `cicpa_status` for CICPAs that were cancelled via the standard
    Frappe Cancel flow (docstatus=2) before before_cancel was updated to do
    this. Without this, the CICPA list view shows `Active` for already-
    cancelled docs, which is confusing.

    LOA quota counters are NOT updated retroactively — admins may have
    already adjusted them manually, and silently shifting numbers could
    surprise users. Only the status label is corrected here.

    Idempotent: only touches rows that are still mismatched.
    """
    frappe.db.sql(
        """
        UPDATE `tabCICPA`
        SET cicpa_status = 'Cancelled'
        WHERE docstatus = 2 AND cicpa_status = 'Active'
        """
    )
