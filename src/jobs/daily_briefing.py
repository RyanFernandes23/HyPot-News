import logging
from src.services.news.gnews import fetch_and_ingest_daily_briefing

logger = logging.getLogger(__name__)


async def run_daily_briefing_job():
    """
    Cron job that fetches GNews articles for daily briefing.
    Runs at 3am UTC (6am IST, 5am WAT, etc - adjust for your timezone).
    """
    logger.info("[Daily Briefing] Starting GNews fetch...")
    try:
        count = await fetch_and_ingest_daily_briefing()
        logger.info(f"[Daily Briefing] Successfully ingested {count} articles")
    except Exception as e:
        logger.error(f"[Daily Briefing] Critical error: {e}", exc_info=True)
