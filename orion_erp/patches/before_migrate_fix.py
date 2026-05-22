import frappe


def replace_in_table(doctype, field, old, new):

    try:

        frappe.db.sql(f"""
            UPDATE `tab{doctype}`
            SET `{field}` = REPLACE(`{field}`, %s, %s)
            WHERE `{field}` LIKE %s
        """, (old, new, f"%{old}%"))

        print(f"Updated {doctype}.{field}")

    except Exception as e:

        print(f"Skipped {doctype}.{field} -> {e}")


def execute():

    frappe.flags.in_patch = True

    print("\n===== BEFORE MIGRATE APP FIX =====\n")

    replacements = [
        ("rental_management.rental_management", "orion_erp"),
        ("rental_management", "orion_erp"),
    ]

    tables_and_fields = {
        "Module Def": ["app_name"],
        "Scheduled Job Type": ["method"],
        "Number Card": ["function"],
        "Singles": ["value"],
        "DefaultValue": ["defvalue"],
        "Server Script": ["script"],
        "Property Setter": ["value"],
        "Notification": ["condition", "message"],
        "Auto Repeat": ["reference_doctype"],
        "Webhook": ["webhook_doctype"],
        "Desktop Icon": ["module_name"],
        "DocType": ["module"],
        "Report": ["module"],
        "Page": ["module"],
    }

    for old, new in replacements:

        print(f"\nReplacing {old} -> {new}\n")

        for doctype, fields in tables_and_fields.items():

            for field in fields:

                replace_in_table(doctype, field, old, new)

    # Explicit installed_apps cleanup
    try:

        frappe.db.sql("""
            UPDATE `tabDefaultValue`
            SET `defvalue` = REPLACE(
                `defvalue`,
                'rental_management',
                'orion_erp'
            )
            WHERE `defkey` = 'installed_apps'
            AND `defvalue` LIKE '%rental_management%'
        """)

        print("Updated DefaultValue.installed_apps")

    except Exception as e:

        print(f"Skipped DefaultValue.installed_apps -> {e}")

    frappe.db.commit()

    frappe.clear_cache()

    frappe.flags.in_patch = False

    print("\n===== BEFORE MIGRATE FIX COMPLETED =====\n")