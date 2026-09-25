# Workshop Module Change Log

This append-only log provides a readable history of Workshop development. Git commits remain the authoritative technical record.

## Categories

`Documentation` · `Schema` · `Workflow` · `Permissions` · `Backend` · `UI` · `Stock` · `Purchase` · `Accounts` · `HR/Fleet` · `Migration` · `Test` · `Fix`

---

## 2026-09-25 16:17 GST (+04:00) — Development foundation

- **Category:** Documentation
- **Repository:** `yousafaj/Orion-ERP`
- **Branch:** `feature/workshop-module`
- **Source branch:** `develop`
- **Source baseline:** `694f629b1b6f58142a617ca2a6dc108605aa9527`
- **Commit:** `b388a18d42ed0e8b9ce6d73fc54a4438ba3c1f27`
- **Files added:** `docs/workshop/technical-baseline.md`, this change log
- **Purpose:** Establish the isolated branch, master-record reuse rules and controlled development process before application code is added.
- **Master-data impact:** None.
- **Database impact:** None.
- **Site impact:** None; staging and production were not accessed or changed.
- **Tests performed:** Confirmed the feature branch resolves to the recorded baseline and confirmed the technical-baseline file was created only on the feature branch.
- **Known issues:** Application code, DocTypes, roles, permissions, workflows and tests have not yet been implemented.
- **Rollback:** Delete the feature branch if the documentation foundation is rejected. Shared branches and sites remain unaffected.
- **Confidentiality:** Only sanitized technical information is kept in this public repository. Internal business requirements remain in the private management record.
- **Status:** Completed

---

## 2026-09-25 16:34 GST (+04:00) — Module, roles and workspace scaffold

- **Category:** Schema / UI
- **Commit:** `d0ce9beeb70460a4cc4a4f238bb76b8bb3eda6d7`
- **Files:** Module registration, setup hook, workspace and package initializers
- **Purpose:** Add the version-controlled Workshop module scaffold.
- **Site impact:** Not deployed or migrated.
- **Tests performed:** Python compilation, JSON parsing and Git whitespace validation passed locally.
- **Rollback:** Revert the commit; use the pre-migration backup if already deployed.
- **Status:** Committed; not deployed

## 2026-09-25 16:34 GST (+04:00) — Workshop Request and Job Card core

- **Category:** Schema / Workflow / Backend / Permissions / Test
- **Commit:** `e0a59f47f481758893f3bbba39babcd2d65f9161`
- **Files:** Core Workshop transaction DocTypes, controllers, client script and tests
- **Purpose:** Add the core Workshop transaction model using Links to existing application masters.
- **Site impact:** Not deployed or migrated.
- **Tests performed:** Python compilation, JSON parsing and Git whitespace validation passed locally. Frappe integration tests were added but could not run outside a Frappe bench.
- **Rollback:** Revert the commit; use the pre-migration backup if already deployed.
- **Status:** Committed; not deployed

## 2026-09-25 16:34 GST (+04:00) — Maintenance plans and inspection templates

- **Category:** Schema / Planning / Test
- **Commit:** `bdc2fe561351ead9c3edd3e9b3115d4051d102b7`
- **Files:** Maintenance planning and inspection-template DocTypes, controllers and tests
- **Purpose:** Add version-controlled planning and inspection structures.
- **Site impact:** Not deployed or migrated.
- **Tests performed:** Python compilation, JSON parsing and Git whitespace validation passed locally; a Frappe integration test covers combined due-date and odometer calculation.
- **Rollback:** Revert the commit; use the pre-migration backup if already deployed.
- **Status:** Committed; not deployed

## 2026-09-25 16:39 GST (+04:00) — Migration ordering safeguard

- **Category:** Fix / Migration
- **Commit:** `b1de8d74146c7363043fe8b3585bef963efdd238`
- **Files:** Workshop setup and application hooks
- **Purpose:** Run idempotent Workshop prerequisites before schema synchronization and verify them again afterward.
- **Site impact:** Not deployed or migrated.
- **Tests performed:** Python compilation and Git whitespace validation passed locally.
- **Rollback:** Revert the commit; use the pre-migration backup if already deployed.
- **Status:** Committed; not deployed

## 2026-09-25 22:39 GST (+04:00) — Staging integration preparation

- **Category:** Integration / Staging safety
- **Merge commit:** `6640e0416ea49c3cd97c4d44023d2b88aeabe589`
- **Parents:** Current Rental Management staging branch and Workshop feature branch
- **Purpose:** Preserve the existing Rental Management staging work while adding the Workshop module on a separate integration branch.
- **Site impact:** A fresh staging backup was completed successfully; the integration branch was merged but not yet deployed or migrated when this entry was recorded.
- **Tests performed:** Merge completed without code conflicts. Python compilation, JSON parsing and Git whitespace validation passed locally. GitHub CI reached application setup but could not install the existing optional S3 integration because the CI bench does not fetch that dependency; the syntax and conflict checks passed.
- **Rollback:** Return staging to its previous Rental Management branch and use the verified pre-migration backup if database restoration is required.
- **Status:** Integration branch merged; deployment pending

---

## 2026-09-25 23:06 GST (+04:00) — Staging deployment and verification

- **Category:** Migration / Permissions / Test
- **Branch:** `feature/staging-workshop-integration-20260925`
- **Deployed commit:** `25853f27f0476114c7f46432b31b88f575b16163`
- **Purpose:** Deploy the isolated integration branch to staging and verify the Workshop schema without creating operational records.
- **Site impact:** Staging deployment and migration completed successfully with zero platform issues. Production, `develop` and `main` were not changed.
- **Verification:** Workshop Request, Workshop Job Card, Vehicle Maintenance Plan and Workshop Inspection Template are available in the Workshop module. Workshop Manager, Workshop Supervisor and Workshop Team exist and are enabled.
- **Data impact:** No Workshop requests, job cards, maintenance plans or inspection templates were created. Existing Vehicle and Employee masters remain authoritative and are linked by the Workshop schema; Asset remains optional.
- **Backup:** A fresh staging database-and-files backup was completed before deployment.
- **Known limitation:** The repository CI environment does not fetch the already-installed S3 Attachment dependency, so its application-install step remains an infrastructure limitation unrelated to the successful Frappe Cloud staging migration.
- **Rollback:** Restore the pre-deployment staging branch and use the verified backup only if site recovery is required.
- **Status:** Deployed and schema-verified on staging; functional UAT remains pending
