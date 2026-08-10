from frappe.model.document import Document


class LeaveDelegationDetail(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        approver_field: DF.Data | None
        delegate_user: DF.Link
        document_name: DF.Link
        employee_name: DF.Data | None
        has_delegation: DF.Check
        level: DF.Int
        parent: DF.Data
        parentfield: DF.Data
        parenttype: DF.Data
        previous_reviewer: DF.Link
    # end: auto-generated types
    pass
