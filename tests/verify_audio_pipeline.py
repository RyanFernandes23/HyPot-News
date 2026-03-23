import os
import sys
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
import asyncio
from src.services.audio.processor import audio_processor
from src.db.supabase import supabase_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_single_article():
    # Pick an existing article from the DB
    article_id = "ee29c831-537c-47d4-8dab-fa107d83153f"
    
    logger.info(f"Testing audio processing for article: {article_id}")
    
    # Fetch the article
    response = supabase_service.table("news_articles").select("*").eq("id", article_id).execute()
    if not response.data:
        logger.error("Article not found in DB.")
        return
        
    article = response.data[0]
    
    # Reset status to pending for testing
    supabase_service.table("news_articles").update({"audio_status": "pending"}).eq("id", article_id).execute()
    
    # Manually trigger processing
    audio_processor.process_article(article)
    
    # Check if DB was updated
    response = supabase_service.table("news_articles").select("*").eq("id", article_id).execute()
    updated_article = response.data[0]
    
    logger.info("Verification Results:")
    logger.info(f"Audio Status: {updated_article['audio_status']}")
    logger.info(f"Headline HLS URL: {updated_article['headline_hls_base_url']}")
    logger.info(f"Summary HLS URL: {updated_article['summary_hls_base_url']}")

if __name__ == "__main__":
    asyncio.run(test_single_article())
