import logging
from src.services.rss.fetcher import fetch_all_feeds
from src.services.rss.ingester import ingest_articles

logger = logging.getLogger(__name__)

async def run_news_fetch_job():
    """
    Periodic job that fetches all RSS feeds, aggregations them,
    writes them to a debug file, and then upserts them into Supabase.
    """
    logger.info("[RSS Job] Starting scheduled fetch round...")
    try:
        entries = await fetch_all_feeds()
        logger.info(f"[RSS Job] Fetched and parsed {len(entries)} total entries.")
        
        count = ingest_articles(entries)
        logger.info(f"[RSS Job] Successfully ingested {count} new or updated articles into the database.")
        
    except Exception as e:
        logger.error(f"[RSS Job] Critical error during job execution: {e}", exc_info=True)
