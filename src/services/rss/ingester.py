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
    url = entry.get("link", "") or entry.get("source_url", "") or entry.get("url", "")
    if url:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()
        
    title = entry.get("title", "") or entry.get("headline", "")
    source = entry.get("descriptor_source", "") or entry.get("source_name", "")
    fallback_string = f"{title}-{source}"
    return hashlib.sha256(fallback_string.encode("utf-8")).hexdigest()

def map_entry_to_article(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps a raw feedparser entry dict or Flutter article payload to the DB schema.
    Ensures that empty strings are replaced with None for timestamp/URL fields to prevent DB errors.
    """
    # 1. Extract image URL
    image_url = entry.get("url_to_image") or entry.get("imageUrl") or ""
    if not image_url:
        if "media_thumbnail" in entry and entry["media_thumbnail"]:
            image_url = entry["media_thumbnail"][0].get("url", "")
        elif "media_content" in entry and entry["media_content"]:
            image_url = entry["media_content"][0].get("url", "")
            
    # 2. Extract source name
    source_name = entry.get("descriptor_source") or entry.get("source_name")
    if not source_name:
        source_obj = entry.get("source")
        if isinstance(source_obj, dict):
            source_name = source_obj.get("title")
        elif isinstance(source_obj, str):
            source_name = source_obj
    source_name = source_name or "Unknown"

    # 3. Extract headline
    headline = entry.get("title") or entry.get("headline") or "No Title"

    # 4. Extract category
    category = entry.get("descriptor_category") or entry.get("category") or "Uncategorized"

    # 5. Extract source URL
    source_url = entry.get("link") or entry.get("source_url") or entry.get("url") or None

    # 6. Extract summary/content
    summary = entry.get("summary") or entry.get("summarized_content") or ""

    # 7. Extract published date
    import time
    from datetime import datetime
    published_at = entry.get("published_at") or entry.get("published")
    
    # If it's a feedparser-style parsed tuple, convert to ISO
    if "published_parsed" in entry and entry["published_parsed"]:
        try:
            published_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry["published_parsed"])
        except:
            published_at = None
    
    # Final check: Ensure we don't send empty strings to timestamp/URL columns
    # Supabase (Postgres) expects valid timestamp or NULL, not ""
    if not published_at or (isinstance(published_at, str) and published_at.strip() == ""):
        published_at = None
    
    return {
        "external_id": build_external_id(entry),
        "source_name": source_name,
        "author": entry.get("author") or None,
        "headline": headline,
        "summarized_content": summary,
        "content": "",
        "source_url": source_url,
        "url_to_image": image_url or None,
        "category": category,
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
            .order("published_at", desc=True) \
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
        
        # After upsert, prune each category to keep only 5 articles
        # and collect the IDs of those 5 for processing.
        surviver_ids = []
        for category in categories_to_prune:
            prune_articles_by_category(category, limit=5)
            
            # Fetch the top 5 remaining articles for this category
            survivors = supabase_service.table("news_articles") \
                .select("id") \
                .eq("category", category) \
                .order("published_at", desc=True) \
                .limit(5) \
                .execute()
            
            if survivors.data:
                surviver_ids.extend([row["id"] for row in survivors.data])
            
        # Trigger immediate audio generation tasks for only the surviving top articles
        from src.actors import process_audio_task
        for article_id in set(surviver_ids): # Set for safety
            # We send the task for the top 5; the actor will skip if it's already 'ready'
            process_audio_task.send(article_id)
            
        return len(response.data) if response.data else 0
        
    except Exception as e:
        logger.error(f"Batch upsert failed: {e}")
        return 0
