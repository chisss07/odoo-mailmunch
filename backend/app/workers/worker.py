from arq import cron
from arq.connections import RedisSettings

from app.config import settings
from app.workers.m365_poller import poll_m365_mailbox
from app.workers.email_processor import process_pending_emails
from app.workers.odoo_sync import sync_po_statuses, refresh_caches


def parse_redis_url(url: str) -> RedisSettings:
    """Parse redis://host:port into RedisSettings."""
    url = url.replace("redis://", "")
    host, port = url.split(":") if ":" in url else (url, "6379")
    return RedisSettings(host=host, port=int(port))


class WorkerSettings:
    functions = [poll_m365_mailbox, process_pending_emails, sync_po_statuses, refresh_caches]

    cron_jobs = [
        cron(poll_m365_mailbox, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
        cron(process_pending_emails, minute={1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56}),
        cron(sync_po_statuses, minute={2, 17, 32, 47}),
        cron(refresh_caches, hour={0, 6, 12, 18}, minute=0),
    ]

    redis_settings = parse_redis_url(settings.redis_url)
