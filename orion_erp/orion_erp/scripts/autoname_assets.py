import frappe
from frappe.utils import now_datetime

def autoname_asset(doc, method=None):
    """
    Build Asset name like:
    ACC-ASS-2025-IT-000001

    Global counter:
    - always increments by 1 across ALL assets
    - does NOT reset per year or per reference number
    """

    # 1. Current year (YYYY)
    current_year = now_datetime().strftime("%Y")

    # 2. Required reference number from the Asset
    ref_no = (getattr(doc, "custom_reference_number", "") or "").strip()
    if not ref_no:
        frappe.throw("Please set Custom Reference Number before saving the Asset.")

    # 3. Prepare prefix (constant per record for display, but NOT for counting)
    #    Example: ACC-ASS-2025-IT-
    series_digits = 6
    series_prefix = f"ACC-ASS-{current_year}-{ref_no}-"

    # 4. Get global count of ALL assets created so far
    asset_count = frappe.db.sql(
        """
        SELECT COUNT(*) AS cnt
        FROM `tabAsset`
        """,
        as_dict=True,
    )

    existing = asset_count[0]["cnt"] if asset_count else 0
    next_number = existing + 1

    # 5. Zero-pad and assign final name
    counter_str = str(next_number).zfill(series_digits)
    doc.name = f"{series_prefix}{counter_str}"