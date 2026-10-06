# Office annual-leave allocation adjustment — staging

6 October 2026: the office staff audit found historical allocations whose company differs from later accrual ledger entries. Native HRMS filters existing allocation credits by company during submitted allocation edits, so an adjustment can repost credits it fails to count.

The Leave Allocation override sums submitted non-carry-forward entries belonging to the same allocation, employee and leave type across companies. It applies only to Office employees and configured projected-accrual leave types. Other leave types and employee categories retain native behavior. All native update permissions and validation remain inherited. Historical ledger entries retain their company and audit trail; this change does not rewrite balances, allocations or attendance.

Seven regression checks cover mixed companies, compensating negative entries, cancelled/draft/unrelated entries, carry-forward separation, expiry, empty ledgers and native fallback. Existing projection and late-attendance checks must also pass. The private employee audit is retained outside this repository.
