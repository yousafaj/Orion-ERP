# rental_management — Claude working notes

## Hard rules

**Never delete a core Frappe or ERPNext doctype, or any stock field on one.**
This includes (non-exhaustive): Employee, Driver, Vehicle, Customer, Supplier,
Asset, Contract, Project, Sales Invoice, Purchase Invoice, Journal Entry,
Address, Contact, Item, Warehouse, Account, Salary Slip, Leave Application,
Timesheet, Designation, Department, Company, Location, etc. — anything that
lives under `apps/frappe/...` or `apps/erpnext/...` (and `apps/hrms/...`).

You **may**:
- Add custom fields and property setters via `custom/<doctype>.json` fixtures.
- Hide stock fields with a Property Setter (`hidden=1`) — reversible.
- Wire `fetch_from` on stock fields via Property Setter.
- Delete records *of* core doctypes only when the user explicitly authorizes it
  for a specific record (not en masse).

You **must not**:
- Edit any JSON under `apps/frappe/` or `apps/erpnext/` or `apps/hrms/`.
- Drop columns backing stock fields (anything not prefixed `custom_` and not
  on a rental_management-owned doctype).
- Run `frappe.delete_doc("DocType", "<core doctype name>")`.

If a task seems to require deleting a core doctype/field, stop and ask.

## Patch convention for cleanup that fixtures can't express

Frappe fixtures are **additive** — removing a Custom Field entry from a
`custom/<doctype>.json` fixture does **not** delete the existing DB record or
its column on the next migrate. When you remove a custom field from a fixture,
also write a Frappe patch under `rental_management/patches/` and register it in
`rental_management/patches.txt` so the cleanup runs once on every site during
`bench migrate`. Make the patch idempotent (check existence before delete /
DROP) so it's safe on partially-cleaned environments.

Same applies to removing a field from a rental_management-owned doctype's JSON
— Frappe doesn't auto-drop the column, so include a `DROP COLUMN IF EXISTS`
in the patch.

## Local dev quirks observed

- `bench start`'s honcho supervisor will kill all child processes if any one
  exits. The `bench schedule` process sometimes races redis on startup and
  exits rc=0, taking the rest down. If `bench start` looks like it shut itself
  off seconds after boot, that's the cause — restart it.
- After editing custom field fixtures and running `bench migrate`, also
  `clear-cache` and hard-refresh the browser (Cmd+Shift+R) to bust cached
  JS/meta.
