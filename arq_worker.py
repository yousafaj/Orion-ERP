import frappe
from arq.connections import RedisSettings

from frappe.utils import cint


REDIS_PORT = cint(frappe.conf.cache_port or 13000) if hasattr(frappe, "conf") else 13000


async def startup(ctx):
	pass


async def shutdown(ctx):
	pass


class WorkerSettings:
	functions = []
	on_startup = startup
	on_shutdown = shutdown
	half_redis_search_max_results = 10000
	burst_max_retry = 3
	max_jobs = 10
	redis_settings = RedisSettings(port=REDIS_PORT)
