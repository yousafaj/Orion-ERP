import frappe
from frappe.desk.form.meta import get_code_files_via_hooks
from frappe.website.doctype.web_form.web_form import WebForm as BaseWebForm


def _get_child_table_fields(doctype: str):
    meta = frappe.get_meta(doctype)
    if not meta:
        return []
    return [f for f in meta.fields]


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
