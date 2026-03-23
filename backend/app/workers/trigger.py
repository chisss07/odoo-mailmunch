import logging
from arq import create_pool
from app.workers.worker import parse_redis_url
from app.config import settings

logger = logging.getLogger(__name__)


async def trigger_email_processing():
    """Enqueue process_pending_emails for immediate execution."""
    try:
        redis = await create_pool(parse_redis_url(settings.redis_url))
        await redis.enqueue_job("process_pending_emails")
        logger.info("Triggered immediate email processing")
    except Exception as e:
        logger.warning(f"Failed to trigger email processing: {e}")
