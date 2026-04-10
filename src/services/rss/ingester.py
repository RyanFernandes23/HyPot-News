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

import re

def extract_image_from_html(html_content: str) -> str:
    """Helper to extract the first img src from an HTML string."""
    if not html_content or not isinstance(html_content, str):
        return ""
    # Look for common image extensions in src
    match = re.search(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|webp|gif|svg)[^"\']*)["\']', html_content, re.IGNORECASE)
    return match.group(1) if match else ""

def map_entry_to_article(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps a raw feedparser entry dict or Flutter article payload to the DB schema.
    Ensures that empty strings are replaced with None for timestamp/URL fields to prevent DB errors.
    """
    # 1. Extract image URL with multiple fallbacks
    image_url = entry.get("url_to_image") or entry.get("imageUrl") or ""
    
    # Fallback A: Media RSS standard tags
    if not image_url:
        if "media_thumbnail" in entry and entry["media_thumbnail"]:
            image_url = entry["media_thumbnail"][0].get("url", "")
        elif "media_content" in entry and entry["media_content"]:
            image_url = entry["media_content"][0].get("url", "")
            
    # Fallback B: Feedparser enclosures
    if not image_url and "enclosures" in entry and entry["enclosures"]:
        for enc in entry["enclosures"]:
            url = enc.get("url", "")
            if enc.get("type", "").startswith("image/") or url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg')):
                image_url = url
                break

    # Fallback C: Feedparser links
    if not image_url and "links" in entry and entry["links"]:
        for link in entry["links"]:
            href = link.get("href", "")
            if link.get("type", "").startswith("image/") or href.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg')):
                image_url = href
                break

    # Fallback D: HTML content/summary (Search for <img> tags)
    if not image_url:
        # Check summary and content
        content_blobs = [entry.get("summary", ""), entry.get("content", "")]
        if "content" in entry and isinstance(entry["content"], list):
            content_blobs.extend([c.get("value", "") for c in entry["content"] if isinstance(c, dict)])
        
        for blob in content_blobs:
            if isinstance(blob, str) and blob:
                found_url = extract_image_from_html(blob)
                if found_url:
                    image_url = found_url
                    break
            
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
        # response.data will contain the rows after upsert (including generated IDs)
        response = supabase_service.table("news_articles").upsert(
            articles_data, 
            on_conflict="external_id"
        ).execute()
        
        return len(response.data)
        
    except Exception as e:
        logger.error(f"Batch upsert failed: {e}")
        return 0
