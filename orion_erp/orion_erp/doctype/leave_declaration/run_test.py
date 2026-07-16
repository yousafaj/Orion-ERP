import frappe
import unittest
import importlib

frappe.flags.in_test = True

mod = importlib.import_module("orion_erp.orion_erp.doctype.leave_declaration.test_leave_declaration")
loader = unittest.TestLoader()
suite = loader.loadTestsFromModule(mod)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
