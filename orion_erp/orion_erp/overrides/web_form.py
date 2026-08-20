import frappe
from frappe import _
from frappe.desk.form.meta import get_code_files_via_hooks
from frappe.utils import cint
from frappe.website.doctype.web_form.web_form import WebForm as BaseWebForm


def _get_child_table_fields(doctype: str):
    meta = frappe.get_meta(doctype)
    if not meta:
        return []
    return [f for f in meta.fields]


def _get_multiselect_target_doctypes(web_form) -> set[str]:
    """Doctypes that are safe to search for this web form's Table MultiSelect fields."""
    doctypes = set()
    for field in web_form.web_form_fields:
        if field.fieldtype == "Table MultiSelect" and field.options:
            child_meta = frappe.get_meta(field.options)
            link_field = next((f for f in child_meta.fields if f.fieldtype == "Link"), None)
            if link_field:
                doctypes.add(link_field.options)
    return doctypes


class CustomWebForm(BaseWebForm):
    def _prepare_table_multiselect(self, web_form_doc):
        for field in web_form_doc.web_form_fields:
            if field.fieldtype == "Table MultiSelect" and not field.fields:
                field.fields = _get_child_table_fields(field.options)

    def load_form_data(self, context):
        super().load_form_data(context)
        self._prepare_table_multiselect(context.web_form_doc)

    def add_custom_context_and_script(self, context):
        super().add_custom_context_and_script(context)
        if not self.is_standard:
            self._include_webform_js(context)

    def _include_webform_js(self, context):
        script = context.get("script") or ""
        for path in get_code_files_via_hooks("webform_include_js", context.doc_type):
            custom_js = frappe.render_template(open(path).read(), context)
            script = "\n\n".join([script, custom_js]) if script else custom_js
        if script:
            context.script = script


@frappe.whitelist(allow_guest=True)
def get_form_data(doctype: str, docname: str | None = None, web_form_name: str | None = None):
    from frappe.website.doctype.web_form.web_form import get_form_data as original

    result = original(doctype, docname, web_form_name)

    web_form = getattr(result, "web_form", None) or result.get("web_form")
    if web_form:
        for field in web_form.web_form_fields:
            if field.fieldtype == "Table MultiSelect" and not field.fields:
                field.fields = _get_child_table_fields(field.options)

    return result


@frappe.whitelist(allow_guest=True)
def search_table_multiselect(web_form_name: str, doctype: str, txt: str = "", page_length: int = 10):
    """Guest-safe search for Table MultiSelect fields on public Web Forms.

    Core's Table MultiSelect control (frappe.ui.form.ControlTableMultiSelect) always
    searches via frappe.desk.search.search_link, which is whitelisted for logged-in
    users only. Web Form's own guest loader (get_form_data) already works around this
    for plain Link fields by preloading options server-side with frappe.get_all
    (frappe.website.doctype.web_form.web_form.get_link_options) - this mirrors that
    same pattern for Table MultiSelect, restricted to only the doctype(s) this
    specific published web form actually references, so it can't be used as an
    open search oracle for arbitrary doctypes.
    """
    web_form = frappe.get_doc("Web Form", web_form_name)

    if not web_form.published:
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if doctype not in _get_multiselect_target_doctypes(web_form):
        frappe.throw(
            _("You don't have permission to access the {0} DocType.").format(doctype),
            frappe.PermissionError,
        )

    meta = frappe.get_meta(doctype)
    show_title = bool(meta.title_field and meta.show_title_field_in_link)

    fields = ["name as value"]
    if show_title:
        fields.append(f"{meta.title_field} as label")

    or_filters = []
    txt = (txt or "").strip()
    if txt:
        or_filters.append(["name", "like", f"%{txt}%"])
        if meta.title_field:
            or_filters.append([meta.title_field, "like", f"%{txt}%"])

    results = frappe.get_all(
        doctype,
        or_filters=or_filters,
        fields=fields,
        page_length=cint(page_length) or 10,
    )

    if show_title:
        return [{"value": r.value, "label": r.get("label"), "description": r.value} for r in results]
    return [{"value": r.value, "description": ""} for r in results]


@frappe.whitelist(allow_guest=True)
def validate_table_multiselect_link(web_form_name: str, doctype: str, docname: str):
    """Guest-safe existence check for a value picked in a Table MultiSelect field.

    Mirrors search_table_multiselect() above: frappe.client.validate_link is also
    whitelisted for logged-in users only, so it throws for anonymous visitors on a
    public web form. Same doctype allow-list restriction applies here.
    """
    web_form = frappe.get_doc("Web Form", web_form_name)

    if not web_form.published:
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if doctype not in _get_multiselect_target_doctypes(web_form):
        frappe.throw(
            _("You don't have permission to access the {0} DocType.").format(doctype),
            frappe.PermissionError,
        )

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("Value {0} missing for {1}").format(docname, doctype))

    return {"name": docname}
