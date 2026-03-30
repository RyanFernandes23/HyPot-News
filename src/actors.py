import dramatiq
import asyncio
import logging
from dramatiq.brokers.redis import RedisBroker
from src.core.config import settings
from src.db.supabase import supabase_service
from src.services.audio.processor import audio_processor

# Configure Logging
logger = logging.getLogger(__name__)

# Initialize Redis Broker
# Standard redisbroker handles rediss:// automatically
redis_broker = RedisBroker(url=settings.REDIS_URL)
dramatiq.set_broker(redis_broker)

@dramatiq.actor(max_retries=3, min_backoff=60000) # 1 minute backoff
def process_audio_task(article_id: str):
    """
    Dramatiq actor to process a single article's audio generation.
    """
    logger.info(f"[Actor] Received audio generation task for article: {article_id}")
    
    try:
        # Fetch latest article data
        response = supabase_service.table("news_articles").select("*").eq("id", article_id).execute()
        articles = response.data
        
        if not articles:
            logger.warning(f"[Actor] Article {article_id} not found in database.")
            return
            
        article = articles[0]
        
        # Check if already processed
        if article.get("audio_status") == "ready":
             logger.info(f"[Actor] Article {article_id} already has audio ready.")
             return

        # Run the async processing logic
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(audio_processor.process_single_article(article))
        finally:
            loop.close()
            
        logger.info(f"[Actor] Successfully completed audio task for: {article_id}")
        
    except Exception as e:
        logger.error(f"[Actor] Error processing audio for {article_id}: {e}")
        # Raising the exception allows Dramatiq to retry based on max_retries
        raise e
