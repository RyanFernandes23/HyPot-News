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
    # Extract image URL
    image_url = ""
    if "media_thumbnail" in entry and entry["media_thumbnail"]:
        image_url = entry["media_thumbnail"][0].get("url", "")
    elif "media_content" in entry and entry["media_content"]:
        image_url = entry["media_content"][0].get("url", "")
        
    # Extract published date
    import time
    published_at = entry.get("published", "")
    if "published_parsed" in entry and entry["published_parsed"]:
        # Convert to ISO format for Postgres/Supabase
        published_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry["published_parsed"])
    
    return {
        "external_id": build_external_id(entry),
        "source_name": entry.get("descriptor_source", "Unknown"),
        "author": entry.get("author", ""),
        "headline": entry.get("title", "No Title"),
        "summarized_content": entry.get("summary", ""),
        "content": "",
        "source_url": entry.get("link", ""),
        "url_to_image": image_url,
        "category": entry.get("descriptor_category", "Uncategorized"),
        "published_at": published_at,
        "raw_data": entry,
    }

def prune_articles_by_category(category: str, limit: int = 5):
    """
    Deletes articles in the given category that are not in the top 'limit'
    when sorted by published_at DESC.
    """
    try:
        # Keep only the latest 5 for each category
        response = supabase_service.table("news_articles") \
            .select("id") \
            .eq("category", category) \
            .order("published_at", {"ascending": False}) \
            .limit(5) \
            .execute()
        
        keep_ids = [row["id"] for row in response.data] if response.data else []
        
        if not keep_ids:
            return
            
        # Delete articles in this category that are NOT in the keep_ids list
        supabase_service.table("news_articles") \
            .delete() \
            .eq("category", category) \
            .not_.in_("id", keep_ids) \
            .execute()
            
        logger.info(f"Pruned articles for category '{category}' to keep only the latest {limit}.")
    except Exception as e:
        logger.error(f"Failed to prune articles for category '{category}': {e}")

def ingest_articles(entries: List[Dict[str, Any]]) -> int:
    """
    Deduplicates and upserts articles into Supabase.
    Returns the number of articles upserted.
    """
    if not entries:
        return 0
        
    unique_articles = {}
    categories_to_prune = set()
    for entry in entries:
        try:
            article = map_entry_to_article(entry)
            unique_articles[article["external_id"]] = article
            categories_to_prune.add(article["category"])
        except Exception as e:
            logger.error(f"Error mapping article {entry.get('title')}: {e}")
            
    articles_data = list(unique_articles.values())
            
    if not articles_data:
        return 0
        
    try:
        # Upsert into Supabase.
        response = supabase_service.table("news_articles").upsert(
            articles_data, 
            on_conflict="external_id"
        ).execute()
        
        # After upsert, prune each category to keep only 10 articles
        for category in categories_to_prune:
            prune_articles_by_category(category, limit=10)
            
        return len(response.data) if response.data else 0
        
    except Exception as e:
        logger.error(f"Batch upsert failed: {e}")
        return 0
