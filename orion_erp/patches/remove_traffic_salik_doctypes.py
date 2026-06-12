import frappe


def execute():
    """NEUTRALIZED — intentionally a no-op.

    This patch previously DROPPED the "Traffic Fine or Accident", "Accident Logs",
    "Salik or Darbs" and "Fines cdt" doctypes and their underlying tables. The
    business has since decided these doctypes are core to the fleet workflow
    (accident/fine tracking and monthly Salik/Darb toll billing), so they must
    NEVER be removed.

    The patch is de-registered from patches.txt and its body reduced to a no-op
    (mirroring the precedent set for delete_all_attendance_sql.py) so that:
      * it cannot run again and drop the tables, and
      * sites that already recorded it in `tabPatch Log` stay consistent.

    Do not re-enable. If these doctypes ever genuinely need removal, write a new,
    clearly-named, reviewed patch instead.
    """
    pass
