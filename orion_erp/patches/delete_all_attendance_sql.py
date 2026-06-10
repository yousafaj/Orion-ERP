import frappe


def execute():
	"""DISABLED — previously ran an unconditional `DELETE FROM `tabAttendance``,
	which wipes ALL attendance records with no filter.

	It has been de-registered from patches.txt and neutralised to a no-op to
	prevent accidental, irreversible data loss on fresh sites, restored
	databases, or sites whose Patch Log was reset. Do not re-enable without
	scoping the delete (date range / company) and an explicit confirmation guard.
	"""
	pass
