import hashlib
import logging
from typing import List, Dict, Any

from src.db.supabase import supabase_service

logger = logging.getLogger(__name__)

def build_external_id(entry: Dict[str, Any]) -> str:
    """
    Builds a unique external_id for deduplication.
    Prefers SHA-256 of the URL.
    Falls back to SHA-256 of title + source if URL is missing.
    """
    url = entry.get("link", "")
    if url:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()
        
    title = entry.get("title", "")
    source = entry.get("descriptor_source", "")
    fallback_string = f"{title}-{source}"
    return hashlib.sha256(fallback_string.encode("utf-8")).hexdigest()

def map_entry_to_article(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps a raw feedparser entry dict to the DB schema for news_articles.
    """
    return {
        "external_id": build_external_id(entry),
        "source_name": entry.get("descriptor_source", "Unknown"),
        "author": entry.get("author", ""),
        "headline": entry.get("title", "No Title"),
        "summarized_content": entry.get("summary", ""),
        "content": "",
        "source_url": entry.get("link", ""),
        "category": entry.get("descriptor_category", "Uncategorized"),
        "raw_data": entry,
    }

def ingest_articles(entries: List[Dict[str, Any]]) -> int:
    """
    Deduplicates and upserts articles into Supabase.
    Returns the number of articles upserted.
    """
    if not entries:
        return 0
        
    unique_articles = {}
    for entry in entries:
        try:
            article = map_entry_to_article(entry)
            unique_articles[article["external_id"]] = article
        except Exception as e:
            logger.error(f"Error mapping article {entry.get('title')}: {e}")
            
    articles_data = list(unique_articles.values())
            
    if not articles_data:
        return 0
        
    try:
        # Upsert into Supabase.
        # on_conflict="external_id" ensures that if the article already exists,
        # it updates it (or just ignores if we didn't change anything).
        # We process in a single batch.
        response = supabase_service.table("news_articles").upsert(
            articles_data, 
            on_conflict="external_id"
        ).execute()
        
        # response.data contains the returned rows
        return len(response.data) if response.data else 0
        
    except Exception as e:
        logger.error(f"Batch upsert failed: {e}")
        return 0
