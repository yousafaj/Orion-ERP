import importlib.util
import sys
import types
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock

frappe=types.ModuleType('frappe')
frappe._=lambda x:x
frappe.PermissionError=PermissionError
frappe.whitelist=lambda:lambda fn:fn
class ValidationError(Exception): pass
def fail(message,*args): raise (args[0] if args else ValidationError)(message)
frappe.throw=fail
utils=types.ModuleType('frappe.utils')
utils.getdate=lambda x: date.fromisoformat(str(x))
utils.nowdate=lambda:'2026-10-02'
sys.modules['frappe']=frappe;sys.modules['frappe.utils']=utils
spec=importlib.util.spec_from_file_location('assignment',Path(__file__).parents[1]/'orion_erp/orion_erp/services/driver_assignment.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class ChangeTests(unittest.TestCase):
 def setUp(self):
  self.m=types.SimpleNamespace(name='VM-TEST',driver='OLD',docstatus=1,rental_status='Active',movement_date='2026-10-01',vehicle='TEST-V',project_to='TEST-P',check_permission=Mock(),db_set=Mock(),add_comment=Mock())
  self.c=types.SimpleNamespace(name='DM-TEST',vehicle_movement='VM-TEST',previous_driver='OLD',driver='NEW',date='2026-10-02',reason='Test replacement',mobilization_status='Change Driver')
  self.e=types.SimpleNamespace(status='Active',custom_employee_category='Non-Office',designation='Heavy Driver',employment_type='Full-time')
  frappe.db=Mock();frappe.db.get_value.return_value=self.e;frappe.db.sql.return_value=[]
  frappe.has_permission=Mock(return_value=True);frappe.get_doc=Mock(return_value=self.m)
 def reject(self):
  with self.assertRaises(ValidationError):a.validate_change(self.c,self.m)
 def test_valid(self):
  a.validate_change(self.c,self.m);self.assertEqual(self.c.vehicle,'TEST-V');self.assertEqual(self.c.project,'TEST-P');self.m.check_permission.assert_called_once_with('write')
 def test_closed(self):self.m.rental_status='Closed';self.reject()
 def test_draft(self):self.m.docstatus=0;self.reject()
 def test_ineligible(self):
  for field,value in [('status','Left'),('custom_employee_category','Office'),('designation','Accountant')]:
   old=getattr(self.e,field);setattr(self.e,field,value);self.reject();setattr(self.e,field,old)
 def test_conflict(self):frappe.db.sql.return_value=[('OTHER',)];self.reject()
 def test_stale(self):self.c.previous_driver='STALE';self.reject()
 def test_noop(self):self.c.driver='OLD';self.reject()
 def test_remove(self):
  self.c.driver=None;self.c.mobilization_status='Demobilize';frappe.db.sql.return_value=[dict(driver='OLD',docstatus=1,rental_status='Active')];a.apply_change(self.c);self.m.db_set.assert_called_once_with('driver',None,update_modified=True);self.assertEqual(self.c.previous_driver,'OLD')
 def test_initial(self):self.m.driver=None;self.c.previous_driver=None;a.validate_change(self.c,self.m)
 def test_dates(self):
  for d in ['2026-10-01','2026-10-03']:self.c.date=d;self.reject()
  self.c.date='2026-10-02';self.m.movement_date='2026-10-03';self.reject()
 def test_employee_permission(self):
  frappe.has_permission.return_value=False
  with self.assertRaises(PermissionError):a.validate_change(self.c,self.m)
  self.m.db_set.assert_not_called()
 def test_locked_latest(self):
  frappe.db.sql.side_effect=[[],[dict(driver='CHANGED',docstatus=1,rental_status='Active')]]
  with self.assertRaises(ValidationError):a.apply_change(self.c)
  self.m.db_set.assert_not_called()
 def test_reason_and_api_permission(self):
  self.c.reason=' ';self.reject();frappe.has_permission.return_value=False
  with self.assertRaises(PermissionError):a.change_driver('VM-TEST',driver='NEW',previous_driver='OLD',reason='Test')
if __name__=='__main__':unittest.main()
