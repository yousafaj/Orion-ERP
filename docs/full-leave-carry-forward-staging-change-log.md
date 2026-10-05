# Full annual leave carry-forward — staging

Approved 5 October 2026: unused accrued annual leave remains available across the service anniversary without the previous 15-day ceiling.

Implementation: match HRMS zero-limit semantics in the projected balance and anniversary carry-forward scheduler. Positive ceilings remain enforced, disabled carry-forward remains disabled, and negative balances do not carry. Pending and posted leave commitments remain deducted; no extra accrual is invented. The form and validation message describe full carry-forward accurately.

Staging configuration after deployment: ANNUAL LEAVE maximum_carry_forwarded_leaves changes from 15 to 0, with is_carry_forward still enabled and the existing zero expiry unchanged. This configuration is staging only; no migration changes production settings. Existing requests and posted allocations are not altered.

Regression checks cover full carry-forward, pending reservations, disabled carry-forward, cross-year requests, and actual scheduler posting without excess. Live validation results are recorded in the pull request after deployment.
