"""Installation hooks.

Currently a no-op — the app reads passport details from whatever shape the
Employee record uses (top-level fields OR a Certificates-style child table)
via the runtime resolver in rental_management.passport_management.utils.

Kept as a stable entry point so we can wire in idempotent setup later
without changing hooks.py.
"""


def after_install():
    pass


def after_migrate():
    pass
