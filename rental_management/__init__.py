__version__ = "0.0.1"

# Monkey patch
from frappe.core.doctype.file.file import File
from rental_management.rental_management.override.files import is_remote_file,get_full_path
File.is_remote_file = property(is_remote_file)
File.get_full_path = get_full_path
