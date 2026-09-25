import frappe


def execute():
    """Historical patch retained for migration compatibility.

    Rental Management is now a source-controlled workspace. Its configuration
    is applied after migration; this patch must never delete it.
    """
    pass
