from frappe.core.doctype.file.file import File

_original_is_remote_file = File.is_remote_file
_original_get_full_path = File.get_full_path


def is_remote_file(self):
    if self.file_url and (
        "/api/method/frappe_s3_attachment" in self.file_url
        or self.file_url.startswith(("http://", "https://"))
    ):
        return True

    return _original_is_remote_file.fget(self)


def get_full_path(self):
    if self.file_url and "/api/method/frappe_s3_attachment" in self.file_url:
        return self.file_url

    return _original_get_full_path(self)