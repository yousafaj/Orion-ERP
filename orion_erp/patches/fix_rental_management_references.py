import frappe
from frappe.utils.background_jobs import get_jobs


def replace_in_table(doctype, field, old, new):
    try:
        table = f"tab{doctype}"

        frappe.db.sql(f"""
            UPDATE `{table}`
            SET `{field}` = REPLACE(`{field}`, %s, %s)
            WHERE `{field}` LIKE %s
        """, (old, new, f"%{old}%"))

        print(f"Updated {doctype}.{field}")

    except Exception as e:
        print(f"Skipped {doctype}.{field} -> {e}")


def execute():

    replacements = [
        ("rental_management.rental_management", "orion_erp"),
        ("rental_management.", "orion_erp."),
        ("rental_management", "orion_erp"),
        ("Rental-Management", "Orion ERP"),
        ("orion_erp.orion_erp", "orion_erp"),
    ]

    tables_and_fields = {
        "Scheduled Job Type": ["method"],
        "Number Card": ["function"],
        "Singles": ["value"],
        "Server Script": ["script"],
        "Property Setter": ["value"],
        "Workspace": ["content"],
        "Notification": ["condition", "message"],
        "Auto Repeat": ["reference_doctype"],
        "Webhook": ["webhook_doctype"],
        "Desktop Icon": ["module_name"],
        "Module Def": ["name", "app_name"],
        "DocType": ["module"],
        "Report": ["module"],
        "Page": ["module"],
        "Workspace Link": ["link_to"],
        "Custom DocPerm": ["parent"],
        "Notification Log": ["subject", "email_content"],
        "Prepared Report": ["report_name"],
        "File": ["file_url"],
        "Error Log": ["method"],
    }

    print("\n========== STARTING FULL CLEANUP ==========\n")

    for old, new in replacements:

        print(f"\nReplacing: {old} --> {new}\n")

        for doctype, fields in tables_and_fields.items():

            for field in fields:
                replace_in_table(doctype, field, old, new)

    # Deep DB Cleanup (dynamic scan)
    print("\n========== SCANNING FULL DATABASE ==========\n")

    try:

        tables = frappe.db.sql("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
        """, as_list=True)

        for (table_name,) in tables:

            try:

                columns = frappe.db.sql("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                    AND table_name = %s
                """, table_name, as_dict=True)

                for column in columns:

                    column_name = column.column_name
                    data_type = str(column.data_type).lower()

                    if data_type not in (
                        "varchar",
                        "text",
                        "longtext",
                        "mediumtext",
                        "char"
                    ):
                        continue

                    for old, new in replacements:

                        try:

                            exists = frappe.db.sql(f"""
                                SELECT *
                                FROM `{table_name}`
                                WHERE `{column_name}` LIKE %s
                                LIMIT 1
                            """, (f"%{old}%",))

                            if exists:

                                frappe.db.sql(f"""
                                    UPDATE `{table_name}`
                                    SET `{column_name}` = REPLACE(`{column_name}`, %s, %s)
                                    WHERE `{column_name}` LIKE %s
                                """, (old, new, f"%{old}%"))

                                print(f"Deep Updated {table_name}.{column_name}")

                        except Exception:
                            pass

            except Exception:
                pass

    except Exception as e:
        print(f"Deep Scan Failed -> {e}")

    # force-fix known methods
    force_fix_queries = [
        (
            "rental_management.rental_management.validations.number_cards.expire_in_30_days",
            "orion_erp.validations.number_cards.expire_in_30_days"
        ),
        (
            "rental_management.rental_management.validations.number_cards.expire_in_60_days",
            "orion_erp.validations.number_cards.expire_in_60_days"
        ),
        (
            "rental_management.rental_management.validations.number_cards.expired",
            "orion_erp.validations.number_cards.expired"
        ),
        (
            "rental_management.tasks.daily.daily",
            "orion_erp.tasks.daily.daily"
        ),
    ]

    for old, new in force_fix_queries:

        try:
            frappe.db.sql("""
                UPDATE `tabNumber Card`
                SET function = %s
                WHERE function = %s
            """, (new, old))
        except Exception:
            pass

        try:
            frappe.db.sql("""
                UPDATE `tabScheduled Job Type`
                SET method = %s
                WHERE method = %s
            """, (new, old))
        except Exception:
            pass

        try:
            frappe.db.sql("""
                UPDATE `tabSingles`
                SET value = REPLACE(value, %s, %s)
                WHERE value LIKE %s
            """, (old, new, f"%{old}%"))
        except Exception:
            pass

        print(f"Force fixed: {old}")

    # clear scheduler logs
    try:
        frappe.db.sql("""
            DELETE FROM `tabScheduled Job Log`
            WHERE method LIKE '%rental_management%'
        """)
        print("Cleared Scheduled Job Logs")
    except Exception as e:
        print(f"Skipped Scheduled Job Log cleanup -> {e}")

    # clear background task tables
    background_tables = [
        "tabRQ Job",
        "tabRQ Worker",
        "tabBackground Task"
    ]

    for table in background_tables:

        try:
            frappe.db.sql(f"""
                DELETE FROM `{table}`
                WHERE job_name LIKE '%rental_management%'
            """)
            print(f"Cleaned {table}")

        except Exception:
            pass

    # clear rq jobs
    try:
        jobs = get_jobs()

        for queue in jobs:
            for job_id, job in jobs[queue].items():

                try:

                    job_text = (
                        str(job.kwargs)
                        + str(job.description)
                        + str(job.func_name)
                    )

                    if (
                        "rental_management" in job_text
                        or "orion_erp.orion_erp" in job_text
                    ):

                        job.cancel()
                        print(f"Cancelled Job: {job_id}")

                except Exception:
                    pass

    except Exception as e:
        print(f"RQ cleanup skipped -> {e}")

    # final verification
    print("\n========== VERIFYING REMAINING REFERENCES ==========\n")

    verification_queries = [
        ("Scheduled Job Type", "method"),
        ("Number Card", "function"),
        ("Singles", "value"),
        ("Server Script", "script"),
        ("Workspace", "content"),
    ]

    for doctype, field in verification_queries:

        try:

            rows = frappe.db.sql(f"""
                SELECT name, `{field}`
                FROM `tab{doctype}`
                WHERE `{field}` LIKE '%rental_management%'
                OR `{field}` LIKE '%orion_erp.orion_erp%'
            """, as_dict=True)

            if rows:

                print(f"\nRemaining in {doctype}.{field}")

                for row in rows:
                    print(row)

        except Exception:
            pass

    frappe.db.commit()

    frappe.clear_cache()

    try:
        frappe.clear_last_message()
    except Exception:
        pass

    print("\n========== FULL CLEANUP COMPLETED ==========\n")