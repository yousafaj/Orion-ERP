# Staging driver changes — 2026-10-02

Baseline: 08ed84f9daa74cdff5e1e7054212702c3286a50a on feature/staging-workshop-integration-20260925.
Feature branch: fix/staging-driver-changes-20261002.

Driver Movement now uses eligible operational Employees and records replacement/removal history against a submitted active Vehicle Movement. Change Driver and Driver History actions are available on active assignments; Rental Management includes Driver Changes.

Submission checks parent write permission, transaction create/submit permissions, employee read access, current assignment, driver eligibility, conflicts, reason, and effective date. Only today's effective changes can apply, never before the rental starts. Future drafts may be saved. Submitted history cannot be cancelled or deleted; corrections use a new change. Employee HR status and Vehicle rental state are unchanged by a driver-only change.

Master and assignment row locks serialize assignment checks with rental creation. All changes and history submission run within the same request transaction.

Migration syncs scoped Driver Movement permissions for existing System Manager, Operation Team and Rental Management roles. It does not change HR User salary permissions.

Validation: 13 standalone behavioral tests passed, Python compile and both JavaScript syntax checks passed. Full Frappe integration and role-specific UAT remain required on staging. No production/main/develop changes.

Deployment: take and verify a fresh staging database/files backup, deploy only Orion ERP from the staging integration branch, migrate without skipping failed patches, then verify schema, permissions and UI. If deployment fails, preserve history and restore the prior app revision; database restore requires separate review to avoid losing later changes.
