# Leave applications spanning annual service years — staging

Branch: `fix/staging-cross-year-leave-20261002`

A future request beginning in the current annual allocation and ending in the
next service year previously raised an allocation-date error. The earlier
forecast supported requests wholly inside either year.

The validator now splits the request at the service-year boundary and checks
each portion. It subtracts the closing-year portion before applying the existing
carry-forward ceiling, counts holidays and the half-day through native helpers,
and reserves only each pending request's intersection with the relevant year.
Own submitted ledger debits are restored by period for repeat validation.
Separate ledger posting uses the same half-day split and retains the guard
against non-consecutive allocations.

The form explains both portions, the next-year balance and the carry-forward
limit. For a request spanning years, the accrual label states that the forecast
runs through the annual transition, including the closing-month credit, rather
than implying that every credit is due before the request starts. No future allocation or earned credit is posted early and no policy
limit is changed. Overlapping allocations and requests beyond the following
service year remain blocked for HR review.

Example: with a 13 January anniversary, a request for 8–27 January uses 5 days
in the closing year and 15 in the following year. It passes when both balances
are sufficient. Extending it to 28 January requires 16 days in the following
year and fails if the carry-forward limit is 15 with no new credit yet due.

Validation: 34 projection/eligibility tests and 5 late-attendance simulations;
Python compilation, JavaScript syntax and CRLF-aware whitespace checks.
Deployment and live validation results are recorded in the pull request.
