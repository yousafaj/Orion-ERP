# Copyright (c) 2026, Orion ERP and Contributors
# See license.txt
"""Guard test: every orion_erp doctype with real controller logic must ship a
real ``test_<doctype>.py`` (not an empty ``pass`` stub).

This is what makes "any new doctype/workflow gets tests" self-enforcing: when a
new logic-bearing doctype is added without tests, this test fails in CI.

The ``PENDING`` set lists logic controllers that are *known* to still lack tests.
Removing one from ``PENDING`` once you write its tests is encouraged (a second
check fails if a PENDING entry already has real tests, to keep the list honest).
A brand-new doctype is NOT on this list, so it cannot slip through untested.
"""

import os
import re

from frappe.tests.utils import FrappeTestCase

import orion_erp

# Logic-bearing doctypes that still need real tests. SHRINK this list over time;
# do NOT grow it for new doctypes — write tests for those instead.
PENDING = {
	"additional_deduction",
	"employee_deduction",
	"process_employee_deductions",
	"leave_settlement",
	"driver_movement",
	"passport_movement",
	"traffic_fine_or_accident",
	"existing_certificates",
	"cicpa_logs",
	"orion_settings",
	"leave_delegation",
}

# Document lifecycle hooks that signal "this controller has real logic".
LIFECYCLE_METHODS = (
	"validate",
	"before_save",
	"before_submit",
	"on_submit",
	"on_update",
	"on_update_after_submit",
	"on_cancel",
	"before_cancel",
	"on_trash",
	"autoname",
)


def _read(path: str) -> str:
	with open(path, encoding="utf-8") as f:
		return f.read()


def _has_logic(controller_src: str) -> bool:
	return any(re.search(rf"\n\s*def {m}\s*\(", controller_src) for m in LIFECYCLE_METHODS)


def _is_stub(test_src: str) -> bool:
	# A real test module defines at least one `def test_...` method.
	return "def test_" not in test_src


def _scan_controllers() -> dict:
	"""Map each doctype folder -> {'logic': bool, 'stub': bool} across orion_erp."""
	app_dir = os.path.dirname(orion_erp.__file__)
	found = {}
	for root, _dirs, _files in os.walk(app_dir):
		folder = os.path.basename(root)
		if folder == "__pycache__":
			continue
		controller = os.path.join(root, f"{folder}.py")
		schema = os.path.join(root, f"{folder}.json")
		# A doctype folder has both <name>.py (controller) and <name>.json (schema).
		if not (os.path.isfile(controller) and os.path.isfile(schema)):
			continue
		test_file = os.path.join(root, f"test_{folder}.py")
		test_src = _read(test_file) if os.path.isfile(test_file) else ""
		found[folder] = {"logic": _has_logic(_read(controller)), "stub": _is_stub(test_src)}
	return found


class TestControllersHaveTests(FrappeTestCase):
	def test_logic_controllers_have_real_tests(self):
		scan = _scan_controllers()
		untested = sorted(
			name
			for name, info in scan.items()
			if info["logic"] and info["stub"] and name not in PENDING
		)
		self.assertFalse(
			untested,
			"These orion_erp doctypes have controller logic but only a stub test. "
			"Write a real test_<doctype>.py for each (see orion_erp/tests/test_template.py). "
			f"Untested: {untested}",
		)

	def test_pending_list_is_not_stale(self):
		scan = _scan_controllers()
		# A PENDING entry that now HAS real tests should be removed from PENDING.
		stale = sorted(name for name in PENDING if name in scan and not scan[name]["stub"])
		self.assertFalse(
			stale,
			f"These doctypes now have real tests — remove them from PENDING: {stale}",
		)
