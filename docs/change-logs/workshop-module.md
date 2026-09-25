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
