import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, add_days, add_months, today
from datetime import timedelta


class TestLeaveSettlementTicketAllowance(FrappeTestCase):
    def setUp(self):
        self.employee = self._create_fresh_employee()
        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    def _months_between(self, from_date, to_date):
        months = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)
        if to_date.day < from_date.day:
            months -= 1
        return max(0, months)

    def _total_months_in_cycle(self, from_date, to_date):
        months = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)
        if to_date.day >= from_date.day:
            months += 1
        return max(1, months)

    def _create_fresh_employee(self):
        emp_name = "TA-TEST-" + str(int(frappe.utils.now_datetime().timestamp() * 1000))
        doj = add_days(today(), -400)
        frappe.db.sql(
            "INSERT INTO `tabEmployee`"
            "(name, employee_name, date_of_joining, company, status, designation, docstatus, creation, modified)"
            " VALUES (%s, %s, %s, %s, %s, %s, 0, NOW(), NOW())",
            (emp_name, "Test TA Employee", doj,
             frappe.db.get_single_value("Global Defaults", "default_company") or "Test",
             "Active", "Manager")
        )
        frappe.db.commit()
        return emp_name

    def _create_ticket_allowance_detail(self, employee_name, from_date, to_date, amount, paid=0, paid_amount=0, manual_paid=0):
        max_idx = frappe.db.get_value(
            "Ticket Allowance Detail",
            {"parent": employee_name, "parenttype": "Employee"},
            "max(idx)"
        ) or 0

        doc = frappe.get_doc({
            "doctype": "Ticket Allowance Detail",
            "parent": employee_name,
            "parentfield": "custom_ticket_allowance_detail",
            "parenttype": "Employee",
            "from_date": from_date,
            "to_date": to_date,
            "amount": amount,
            "outstanding_amount": amount - paid_amount,
            "paid": paid,
            "paid_amount": paid_amount,
            "manual_paid": manual_paid,
            "pro_rata_amount": 0,
            "idx": max_idx + 1
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name

    def test_vacation_settlement_only_completed_periods(self):
        doj = getdate(add_days(today(), -400))
        settlement_date = today()

        cycle1_from = doj
        cycle1_to = add_days(add_months(doj, 12), -1)
        cycle2_from = add_days(cycle1_to, 1)
        cycle2_to = add_days(add_months(cycle2_from, 12), -1)

        self._create_ticket_allowance_detail(self.employee, cycle1_from, cycle1_to, 1200)
        self._create_ticket_allowance_detail(self.employee, cycle2_from, cycle2_to, 1200)

        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(self.employee, settlement_date, "Vacation Settlement")

        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0]["from"]), str(cycle1_from))
        self.assertEqual(str(result[0]["to"]), str(cycle1_to))
        self.assertEqual(result[0]["amount"], 1200)

    def test_vacation_settlement_excludes_current_cycle(self):
        doj = getdate(add_days(today(), -400))
        settlement_date = today()

        cycle1_from = doj
        cycle1_to = add_days(add_months(doj, 12), -1)
        cycle2_from = add_days(cycle1_to, 1)
        cycle2_to = add_days(add_months(cycle2_from, 12), -1)

        self._create_ticket_allowance_detail(self.employee, cycle1_from, cycle1_to, 1200, paid=1, paid_amount=1200)
        self._create_ticket_allowance_detail(self.employee, cycle2_from, cycle2_to, 1200)

        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(self.employee, settlement_date, "Vacation Settlement")

        self.assertEqual(len(result), 0)

    def test_vacation_settlement_excludes_future_cycles(self):
        doj = getdate(add_days(today(), -400))
        settlement_date = today()

        cycle1_from = doj
        cycle1_to = add_days(add_months(doj, 12), -1)
        cycle2_from = add_days(cycle1_to, 1)
        cycle2_to = add_days(add_months(cycle2_from, 12), -1)
        cycle3_from = add_days(cycle2_to, 1)
        cycle3_to = add_days(add_months(cycle3_from, 12), -1)

        self._create_ticket_allowance_detail(self.employee, cycle1_from, cycle1_to, 1200)
        self._create_ticket_allowance_detail(self.employee, cycle2_from, cycle2_to, 1200)
        self._create_ticket_allowance_detail(self.employee, cycle3_from, cycle3_to, 1200)

        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(self.employee, settlement_date, "Vacation Settlement")

        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0]["from"]), str(cycle1_from))

    def test_final_settlement_completed_plus_pro_rata(self):
        doj = getdate(add_days(today(), -400))
        settlement_date = getdate(today())

        cycle1_from = doj
        cycle1_to = add_days(add_months(doj, 12), -1)
        cycle2_from = add_days(cycle1_to, 1)
        cycle2_to = add_days(add_months(cycle2_from, 12), -1)

        self._create_ticket_allowance_detail(self.employee, cycle1_from, cycle1_to, 1200)
        self._create_ticket_allowance_detail(self.employee, cycle2_from, cycle2_to, 1200)

        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(self.employee, settlement_date, "Final Settlement")

        self.assertEqual(len(result), 2)

        completed = result[0]
        self.assertEqual(str(completed["from"]), str(cycle1_from))
        self.assertEqual(completed["amount"], 1200)

        pro_rata_row = result[1]
        self.assertEqual(str(pro_rata_row["from"]), str(cycle2_from))
        self.assertEqual(str(pro_rata_row["to"]), str(settlement_date))

        total_months = self._total_months_in_cycle(cycle2_from, cycle2_to)
        months_elapsed = self._months_between(cycle2_from, settlement_date)
        expected_pro_rata = (1200 / total_months) * months_elapsed
        self.assertAlmostEqual(pro_rata_row["amount"], round(expected_pro_rata, 2), places=2)

    def test_no_ticket_allowance_before_one_year(self):
        emp_name = "TA-NO1Y-" + str(int(frappe.utils.now_datetime().timestamp() * 1000))
        recent_doj = add_days(today(), -200)
        frappe.db.sql(
            "INSERT INTO `tabEmployee`"
            "(name, employee_name, date_of_joining, company, status, designation, docstatus, creation, modified)"
            " VALUES (%s, %s, %s, %s, %s, %s, 0, NOW(), NOW())",
            (emp_name, "No 1 Year Employee", recent_doj,
             frappe.db.get_single_value("Global Defaults", "default_company") or "Test",
             "Active", "Manager")
        )
        frappe.db.commit()

        cycle_from = recent_doj
        cycle_to = add_days(add_months(recent_doj, 12), -1)
        self._create_ticket_allowance_detail(emp_name, cycle_from, cycle_to, 1200)

        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(emp_name, today(), "Final Settlement")
        self.assertEqual(len(result), 0)

    def test_pro_rata_calculation_accuracy(self):
        doj = getdate("2025-02-01")
        emp_name = "TA-PRORATA-" + str(int(frappe.utils.now_datetime().timestamp() * 1000))
        frappe.db.sql(
            "INSERT INTO `tabEmployee`"
            "(name, employee_name, date_of_joining, company, status, designation, docstatus, creation, modified)"
            " VALUES (%s, %s, %s, %s, %s, %s, 0, NOW(), NOW())",
            (emp_name, "Pro Rata Employee", doj,
             frappe.db.get_single_value("Global Defaults", "default_company") or "Test",
             "Active", "Manager")
        )
        frappe.db.commit()

        cycle1_from = doj
        cycle1_to = getdate("2026-01-31")
        cycle2_from = getdate("2026-02-01")
        cycle2_to = getdate("2027-01-31")

        self._create_ticket_allowance_detail(emp_name, cycle1_from, cycle1_to, 1200)
        self._create_ticket_allowance_detail(emp_name, cycle2_from, cycle2_to, 1200)

        settlement_date = getdate("2026-07-19")

        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(emp_name, settlement_date, "Final Settlement")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["amount"], 1200)

        total_months = self._total_months_in_cycle(cycle2_from, cycle2_to)
        months_elapsed = self._months_between(cycle2_from, settlement_date)
        expected_pro_rata = (1200 / total_months) * months_elapsed
        self.assertAlmostEqual(result[1]["amount"], round(expected_pro_rata, 2), places=2)

    def test_internal_transfer_uses_vacation_logic(self):
        doj = getdate(add_days(today(), -400))
        settlement_date = today()

        cycle1_from = doj
        cycle1_to = add_days(add_months(doj, 12), -1)
        cycle2_from = add_days(cycle1_to, 1)
        cycle2_to = add_days(add_months(cycle2_from, 12), -1)

        self._create_ticket_allowance_detail(self.employee, cycle1_from, cycle1_to, 1200)
        self._create_ticket_allowance_detail(self.employee, cycle2_from, cycle2_to, 1200)

        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(self.employee, settlement_date, "Internal Transfer Settlement")

        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0]["from"]), str(cycle1_from))

    def test_empty_employee_returns_empty(self):
        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance("", today(), "Final Settlement")
        self.assertEqual(result, [])

    def test_empty_settlement_date_returns_empty(self):
        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(self.employee, "", "Final Settlement")
        self.assertEqual(result, [])

    def test_no_ticket_detail_returns_empty(self):
        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(self.employee, today(), "Final Settlement")
        self.assertEqual(result, [])

    def test_final_settlement_subtracts_already_paid(self):
        doj = getdate(add_days(today(), -400))
        settlement_date = getdate(today())

        cycle1_from = doj
        cycle1_to = add_days(add_months(doj, 12), -1)
        cycle2_from = add_days(cycle1_to, 1)
        cycle2_to = add_days(add_months(cycle2_from, 12), -1)

        self._create_ticket_allowance_detail(self.employee, cycle1_from, cycle1_to, 1200)
        self._create_ticket_allowance_detail(
            self.employee, cycle2_from, cycle2_to, 1200,
            paid=0, paid_amount=50
        )

        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(self.employee, settlement_date, "Final Settlement")

        total_months_cycle2 = self._total_months_in_cycle(cycle2_from, cycle2_to)
        months_elap = self._months_between(cycle2_from, settlement_date)
        pro_rata_full = (1200 / total_months_cycle2) * months_elap
        expected_payable = max(0, pro_rata_full - 50)

        self.assertEqual(len(result), 2)

        completed = [r for r in result if r["amount"] == 1200]
        pro_rata = [r for r in result if r["amount"] != 1200]
        self.assertEqual(len(completed), 1)
        self.assertEqual(len(pro_rata), 1)
        self.assertAlmostEqual(pro_rata[0]["amount"], round(expected_payable, 2), places=2)

    def test_final_settlement_zero_payable_when_fully_paid(self):
        doj = getdate(add_days(today(), -400))
        settlement_date = getdate(today())

        cycle1_from = doj
        cycle1_to = add_days(add_months(doj, 12), -1)
        cycle2_from = add_days(cycle1_to, 1)
        cycle2_to = add_days(add_months(cycle2_from, 12), -1)

        self._create_ticket_allowance_detail(self.employee, cycle1_from, cycle1_to, 1200)

        total_months_cycle2 = self._total_months_in_cycle(cycle2_from, cycle2_to)
        months_elap = self._months_between(cycle2_from, settlement_date)
        pro_rata_full = (1200 / total_months_cycle2) * months_elap

        self._create_ticket_allowance_detail(
            self.employee, cycle2_from, cycle2_to, 1200,
            paid=0, paid_amount=pro_rata_full
        )

        from orion_erp.orion_erp.services.leave_settlement import get_ticket_allowance
        result = get_ticket_allowance(self.employee, settlement_date, "Final Settlement")

        self.assertLessEqual(len(result), 2)

        pro_rata_rows = [r for r in result if str(r["from"]) == str(cycle2_from)]
        if pro_rata_rows:
            self.assertLessEqual(pro_rata_rows[0]["amount"], 1)

    def test_pro_rata_update_in_cron(self):
        doj = getdate(add_days(today(), -200))

        cycle_from = doj
        cycle_to = add_days(add_months(doj, 12), -1)

        self._create_ticket_allowance_detail(self.employee, cycle_from, cycle_to, 1200)

        from orion_erp.orion_erp.services.employee import _update_current_cycle_pro_rata
        _update_current_cycle_pro_rata(
            frappe._dict(name=self.employee),
            getdate(today())
        )

        pro_rata = frappe.db.get_value(
            "Ticket Allowance Detail",
            {"parent": self.employee, "from_date": cycle_from},
            "pro_rata_amount"
        )

        total_months = self._total_months_in_cycle(cycle_from, cycle_to)
        months_elapsed = self._months_between(cycle_from, getdate(today()))
        expected = round((1200 / total_months) * months_elapsed, 2)

        self.assertIsNotNone(pro_rata)
        self.assertAlmostEqual(float(pro_rata or 0), expected, places=2)
