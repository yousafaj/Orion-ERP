# Rental management staging change log

Branch: `feature/staging-rental-management-20260925`  
Base: local leave staging branch `36b6f69` (the deployed leave code is retained).  
Environment: OrionGroupStage only. No production release is approved.

| Dubai time | Category | Change | Reason | Verification and state |
| --- | --- | --- | --- | --- |
| 2026-09-25 16:55 | Backup | Took a fresh Frappe Cloud onsite database, public-file and private-file staging backup. | Provide a recovery point before a schema or workspace migration. | Frappe Cloud lists the 4:55 pm backup as Success; 20.75 MB database, 3.25 MB public files and 4.32 MB private files. |
| 2026-09-25 17:05 | Assignment source | Vehicle Mobilization now selects an active Non-Office Employee with a driver designation. It rejects double assignment and keeps Employee HR status unchanged. Billing line shows the employee's name and ID. | Use the existing Employee and Vehicle masters, without creating Driver duplicates. | Local compilation and JavaScript syntax checks passed; staging migration and role testing pending. |
| 2026-09-25 17:05 | Dashboard source | Add a source-controlled Rental Management workspace with permission-aware active-rental rows, vehicle and billing cards and a driver count derived from submitted client rentals. Remove the unsupported idle-driver count and obsolete links; preserve the workspace against its historical delete patch. | Display vehicle, client, employee driver and start date, and avoid misleading old-Driver counts. | Workspace and card JSON parse; staging rendering pending. |
| 2026-09-25 17:25 | GitHub publication | Published the source and this branch log to `feature/staging-rental-management-20260925`, commit `fa6f4066f07381347860f66e49ae69597ccd72a9`. | Keep implementation separate from leave, develop and main. | Branch ref updated without force; source compared with the installed leave code. |
| 2026-09-25 17:25 | Staging deployment | Selected only Orion-ERP for update on OrionGroupStage; did not select Framework, ERPNext, HRMS or FAC, and did not skip failed patches. | Apply the reviewed source to the staging site. | Frappe Cloud deployment started; build and migration result pending. |
| 2026-09-25 17:35 | Staging verification | The deployment and site migration succeeded. Rental Management renders vehicle, billing and compliance cards, active-client rentals and direct record links; the Vehicle Movement driver link now targets Employee. | Confirm the source actually reached staging. | Deploy Success, Issues 0; site Migrate Success at 5:35 pm. Active rentals: none yet; 359 vehicles currently marked Idle. |
| 2026-09-25 17:41 | Card correction | Synchronize the existing With Client Drivers number card to its Employee-based custom method on migrate; tidy the displayed Idle Vehicles label and disable misleading percentage comparisons. | Frappe retained a newer database copy of the old standard card despite the new source JSON. | Existing card still targeted Driver in staging; corrective source prepared for redeployment. |

Known limitation: CICPA.driver still links to the retired Driver master. Vehicle Mobilization explicitly warns users to check an employee's CICPA pass separately until CICPA is migrated. The dashboard only includes submitted, active, invoiceable movements. The old Idle Vehicles count is a Vehicle state count, not a booking availability guarantee.

Rollback: retain the verified 4:55 pm staging backup; switch Orion-ERP back to its previous staging branch and migrate. If schema or workspace state cannot be restored through migration alone, restore the staging backup. Production, develop and main are outside this branch.
