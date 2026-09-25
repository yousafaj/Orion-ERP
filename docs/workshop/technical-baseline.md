# Workshop Module — Technical Baseline

**Feature branch:** `feature/workshop-module`  
**Branch baseline:** `694f629b1b6f58142a617ca2a6dc108605aa9527`  
**Recorded:** 2026-09-25 16:17 GST (+04:00)  
**Status:** Documentation foundation only. No site deployment or migration has occurred.

## Architecture rules

- Workshop is implemented as a module inside the existing `orion_erp` application.
- Existing master records are reused through Frappe Link fields.
- Vehicle remains the single vehicle master.
- Employee remains the single workforce master.
- Asset remains an optional link.
- Existing Company, Supplier, Item, Warehouse, Cost Center and accounting-dimension masters are reused.
- Workshop transactions must never create duplicate master records.

## Planned transactional DocTypes

- Workshop Request
- Workshop Job Card
- Vehicle Maintenance Plan
- Workshop Inspection Template
- Child tables for tasks, labour, parts, services and inspections

## Technical controls

- Prevent overlapping active Workshop jobs for one Vehicle.
- Support vehicles with or without an Asset link.
- Keep management-only values separate from statutory accounting postings.
- Preserve vehicle assignment and status history.
- Apply least-privilege permissions.
- Export approved Frappe configuration as version-controlled DocType JSON, fixtures or migration patches.
- Keep credentials, attachments, personal records and site data out of Git.

## Development controls

- Develop only on `feature/workshop-module`.
- Do not push Workshop changes directly to `develop` or `main`.
- Use small categorized commits and pull-request review.
- Record every meaningful change in `docs/change-logs/workshop-module.md`.
- Require backup, migration review, staging tests and explicit approval before deployment.
- Confidential business requirements remain in the private management record and are not committed to this public repository.
