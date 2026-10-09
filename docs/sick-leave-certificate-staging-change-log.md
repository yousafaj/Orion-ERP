# Sick Leave messages and late medical certificates — staging

9 October 2026. Branch: `fix/staging-sick-leave-certificates-20261009`.

A delayed annual forecast request could display an allocation-date error after
the user switched to Sick Leave. Display-only forecasts now return validation
warnings as data; the form discards stale responses before showing an inline
description. Save/submit validation and annual balance checks remain strict.

Repeated medical-certificate selection/save pop-ups are removed. The form retains
the pending-certificate indicator and existing certificate requirement. Missing
certificates still remain pending for payroll and reminders.

Submitted applications now recompute certificate status before permitted field
updates. Migration permits the read-only computed status to update after submit;
it does not grant additional user roles or change leave approval rights. File
hooks update the final uploaded URL even when status was already Submitted,
preserve application timestamps during upload, and do not clear a replacement
certificate when an older file is removed.

General attachments are not automatically classified as medical certificates.
The saved form offers Select Medical Certificate to explicitly identify an
existing file. The endpoint checks application and file permissions, attachment
scope and cancelled status. Workflow, dates, leave balance and ledger are unchanged.

Regression coverage includes late uploads, general attachments, replacements,
deletions, duplicates, unauthorized and cross-record selection, non-required
types, display-only errors and stale annual responses after switching type.

Deployment and live verification are recorded in the pull request. Staging only.
