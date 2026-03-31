import os
import shutil
import time
import logging
from src.core.config import settings
from src.db.supabase import supabase_service
from src.services.audio.processor import audio_processor

logger = logging.getLogger(__name__)

async def run_audio_generation_job():
    """
    Periodic job that picks up articles with audio_status 'pending'
    and processes them.
    """
    logger.info("[Audio Job] Checking for pending articles...")
    try:
        # Fetch up to 10 articles with 'pending' or 'failed' status for batching.
        # Retries 'failed' articles up to 3 times.
        response = supabase_service.table("news_articles") \
            .select("*") \
            .or_("audio_status.eq.pending,and(audio_status.like.failed%,audio_attempts.lt.3)") \
            .limit(10) \
            .execute()
            
        articles = response.data
        if not articles:
            logger.info("[Audio Job] No pending articles found.")
            return
            
        logger.info(f"[Audio Job] Found {len(articles)} pending articles. Starting batch process...")
        # Process all in one batch
        await audio_processor.process_batch(articles)
            
    except Exception as e:
        logger.error(f"[Audio Job] Error during job execution: {e}")

async def run_briefing_audio_prep():
    """
    Scheduled job to prepare audio for the "Daily Briefing".
    Selects the Top 3 latest articles from each category and sends tasks to Dramatiq.
    """
    from src.actors import process_audio_task
    from src.services.rss.feeds import RSS_FEEDS
    
    logger.info("[Briefing Prep] Starting audio preparation for daily briefing...")
    
    # 1. Get unique categories defined in our RSS feeds
    categories = list(set(f["category"] for f in RSS_FEEDS))
    
    tasks_sent = 0
    limit = settings.MAX_AUDIO_TASKS_PER_CATEGORY
    
    for category in categories:
        try:
            # Fetch top N latest from DB for this category
            response = supabase_service.table("news_articles") \
                .select("id, headline, audio_status") \
                .eq("category", category) \
                .order("published_at", desc=True) \
                .limit(limit) \
                .execute()
                
            if response.data:
                for article in response.data:
                    # Only dispatch if not already processed/ready
                    if article.get("audio_status") != "ready":
                        logger.info(f"[Briefing Prep] Queuing audio for: {article.get('headline')}")
                        process_audio_task.send(article["id"])
                        tasks_sent += 1
                        
        except Exception as e:
            logger.error(f"[Briefing Prep] Error fetching for category {category}: {e}")
            
    logger.info(f"[Briefing Prep] Successfully dispatched {tasks_sent} audio tasks across {len(categories)} categories.")

async def run_temp_cleanup_job():
    """
    Cleans up the temporary audio directory of files older than 1 hour.
    """
    logger.info("[Cleanup Job] Starting temporary file cleanup...")
    temp_dir = settings.TEMP_DIR
    if not os.path.exists(temp_dir):
        return
        
    now = time.time()
    # 20 minutes in seconds
    retention_seconds = 20 * 60 
    
    try:
        if os.path.exists(temp_dir):
            for entry in os.listdir(temp_dir):
                path = os.path.join(temp_dir, entry)
                # Check if it's a directory (we create uuid-based subdirs)
                if os.path.isdir(path):
                    mtime = os.path.getmtime(path)
                    if now - mtime > retention_seconds:
                        logger.info(f"[Cleanup Job] Removing old temp directory: {path}")
                        shutil.rmtree(path)
                        
    except Exception as e:
        logger.error(f"[Cleanup Job] Error during cleanup: {e}")
