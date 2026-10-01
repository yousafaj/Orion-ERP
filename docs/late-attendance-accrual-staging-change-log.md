# Late attendance and future allocation year — staging

Branch: `fix/staging-late-attendance-accrual-20261001`

The September attendance upload occurred after the monthly service anniversary.
The old daily job checked only on that anniversary, so the missed credit was
never retried. A November application was then blocked because the submitted
allocation ended on 26 October.

Changes:

- Reconcile completed months in the current and preceding service year when
  submitted attendance arrives, and retry through the daily scheduler.
- Lock the employee and retain each month's existing description marker, so
  concurrent jobs and retries cannot credit the same month twice.
- Preserve legacy imported opening balances through a persistent baseline in
  the allocation description. Do not reconstruct or reopen expired years.
- Run the same reconciliation once during migration for existing late uploads.
- Permit a forecast into the next annual service year based on the current
  submitted entitlement. Keep native approvals, backdating, date and attendance
  validations, existing carry-forward ceiling and expiry, and pending/approved
  request reservations. No future credit or carry-forward is posted early.
- Explain the projected carry-forward and policy ceiling on the form. Include
  the configured accrual leave type in the next-year selection list.

Validation: 21 projection/eligibility regression tests and 5 late-attendance
integration simulations pass, plus Python compilation and JavaScript syntax.
The original 30-day November request is expected to fail against the existing
15-day carry-forward ceiling. Even unrestricted carry-forward would forecast
27.5 days at 1 November from the current 22.5 plus September and October credits;
it must not silently round that up to 30 or fabricate credits.

Deployment and live verification are recorded in the pull request.
