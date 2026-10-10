import asyncio
import logging
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.services.escalation_service import check_and_escalate_incidents
from app.core.config import settings

logger = logging.getLogger("opspulse.escalation")

# Optional Celery worker integration
try:
    from celery import Celery
    celery_app = Celery("opspulse_worker", broker=settings.REDIS_URL)
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )

    @celery_app.task(name="check_escalation_deadlines")
    def check_escalation_deadlines():
        """Periodic Celery task for Docker Beat / Worker."""
        db = SessionLocal()
        try:
            result = check_and_escalate_incidents(db)
            logger.info("Celery escalation check: %s", result)
            return result
        finally:
            db.close()
except Exception:
    celery_app = None

async def start_in_process_escalation_loop():
    """
    In-process async background loop for FastAPI.
    Guarantees escalation logic runs periodically even without a standalone Celery daemon.
    """
    logger.info("Starting in-process SLA escalation monitor (interval: %ds)...", settings.ESCALATION_CHECK_INTERVAL_SECONDS)
    while True:
        try:
            db = SessionLocal()
            try:
                result = check_and_escalate_incidents(db)
                if result.get("escalated_count", 0) > 0 or result.get("exhausted_count", 0) > 0:
                    logger.info("Escalation cycle evaluated: %s", result)
            finally:
                db.close()
        except Exception as e:
            logger.error("Error in escalation worker cycle: %s", e)

        await asyncio.sleep(settings.ESCALATION_CHECK_INTERVAL_SECONDS)
