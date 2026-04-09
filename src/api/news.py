from fastapi import APIRouter, Query, HTTPException, Depends, Body
import time
from datetime import datetime
from typing import List, Optional
from src.db.supabase import supabase_service
from src.api.deps import get_current_user
from src.services.rss.fetcher import fetch_feed
from src.services.rss.feeds import RSS_FEEDS
from src.services.rss.ingester import map_entry_to_article
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def _clean_article(article: dict) -> dict:
    """Removes internal database fields that are not useful for the client."""
    if not isinstance(article, dict):
        return article
    
    clean = article.copy()
    internal_fields = ["raw_data", "headline_search_vector"]
    for field in internal_fields:
        clean.pop(field, None)
    return clean


@router.get("/news", response_model=None)
async def get_news_by_category(
    category: str = Query(..., description="The category of news to fetch, e.g., 'Technology', 'Finance', 'Startups', 'International'"),
    limit: int = Query(10, ge=1, le=100, description="Number of top articles to fetch"),
    user: dict = Depends(get_current_user)
):
    try:
        user_id = getattr(user, "id", None) or user.get("id")
        
        # 1. Fetch read articles for filtering
        read_response = supabase_service.table("read_articles") \
            .select("external_id") \
            .eq("user_id", user_id) \
            .execute()
        read_ids = [row["external_id"] for row in read_response.data] if read_response.data else []
        
        # 2. Query DB with recency (48h) and category
        from datetime import timedelta
        recency_threshold = (datetime.utcnow() - timedelta(hours=48)).isoformat()
        
        query = supabase_service.table("news_articles") \
            .select("*") \
            .eq("category", category) \
            .gt("published_at", recency_threshold) \
            .order("published_at", desc=True)
            
        if read_ids:
            query = query.not_.in_("external_id", read_ids[:500])
            
        response = query.limit(limit).execute()
        articles = [_clean_article(art) for art in response.data] if response.data else []
        
        return {"category": category, "limit": limit, "count": len(articles), "articles": articles}
    except Exception as e:
        logger.error(f"Error fetching news for category '{category}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching news")

@router.get("/news/search", response_model=None)
async def search_live_news(
    q: str = Query(..., description="The search query text"),
    user: dict = Depends(get_current_user)
):
    """
    Searches for news articles directly from RSS providers (Google News RSS).
    Bypasses the database to provide real-time, global results.
    """
    try:
        if not q.strip():
            return {"count": 0, "articles": [], "query": q}

        # 1. Construct Google News Search RSS URL
        search_url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        
        # 2. Use our existing fetch_feed logic (wrapped in a descriptor)
        descriptor = {
            "url": search_url,
            "source": "RSS Search",
            "category": "Search"
        }
        
        all_entries = await fetch_feed(descriptor)
        
        # 3. Formatter: Ensure results look like our Article model
        # We can reuse part of map_entry_to_article or similar, or just return raw with descriptor enrichment
        # The fetch_feed already adds descriptor_source and descriptor_category
        
        return {
            "query": q,
            "count": len(all_entries),
            "articles": [_clean_article(art) for art in all_entries]
        }
    except Exception as e:
        logger.error(f"Error during live search for '{q}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error during search")

@router.get("/news/briefing", response_model=None)
async def get_daily_briefing(
    interests: Optional[List[str]] = Query(None, description="Optional list of categories to override user interests"),
    limit: int = Query(5, ge=1, le=20, description="Number of articles to fetch per chunk"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user: dict = Depends(get_current_user)
):
    try:
        final_interests = interests
        
        # If no interests provided in query, fetch from DB
        if not final_interests:
            # user might be a dict or a Supabase User object depending on the client version
            user_id = getattr(user, "id", None) or user.get("id")
            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found in token")
            
            user_data = supabase_service.table("users") \
                .select("interests") \
                .eq("id", user_id) \
                .single() \
                .execute()
            
            if user_data.data and user_data.data.get("interests"):
                final_interests = user_data.data["interests"]
            else:
                final_interests = ["International"]

        # Daily briefing requires playable audio, so only return fully processed entries.
        user_id = getattr(user, "id", None) or user.get("id")
        
        response = supabase_service.table("news_articles") \
            .select("*") \
            .in_("category", final_interests) \
            .eq("audio_status", "ready") \
            .order("published_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
             
        articles = response.data if response.data else []
            
        return {
            "interests": final_interests,
            "limit": limit,
            "offset": offset,
            "count": len(articles),
            "articles": [_clean_article(art) for art in articles]
        }
    except Exception as e:
        logger.error(f"Error fetching briefing from DB: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching briefing")

@router.get("/news/live", response_model=None)
async def get_live_news(
    category: str = Query(..., description="The category of news to fetch (now from DB)"),
    limit: int = Query(20, ge=1, le=50, description="Number of items to return"),
    before: Optional[str] = Query(None, description="ISO timestamp cursor for pagination"),
    user: dict = Depends(get_current_user)
):
    """
    Refactored to fetch from DB instead of live RSS.
    Supports paging via the 'before' timestamp.
    """
    try:
        user_id = getattr(user, "id", None) or user.get("id")
        
        # 1. Fetch read articles for filtering
        read_response = supabase_service.table("read_articles") \
            .select("external_id") \
            .eq("user_id", user_id) \
            .execute()
        read_ids = [row["external_id"] for row in read_response.data] if read_response.data else []

        # 2. Determine Categories
        categories = [category]
        if category.lower() == "for you":
            user_data = supabase_service.table("users") \
                .select("interests") \
                .eq("id", user_id) \
                .single() \
                .execute()
            categories = user_data.data.get("interests") if user_data.data else ["International"]

        # 3. Build Query
        from datetime import timedelta
        recency_threshold = (datetime.utcnow() - timedelta(hours=48)).isoformat()
        
        query = supabase_service.table("news_articles") \
            .select("*") \
            .in_("category", categories) \
            .gt("published_at", recency_threshold) \
            .order("published_at", desc=True)
            
        if before:
            query = query.lt("published_at", before)
            
        if read_ids:
            query = query.not_.in_("external_id", read_ids[:500])
            
        response = query.limit(limit).execute()
        articles = [_clean_article(art) for art in response.data] if response.data else []

        # 4. next_cursor
        next_cursor = None
        if articles:
            next_cursor = articles[-1].get("published_at")
            
        return {
            "category": category, 
            "limit": limit,
            "before": before,
            "next_cursor": next_cursor,
            "count": len(articles), 
            "articles": articles
        }
    except Exception as e:
        logger.error(f"Error fetching DB-backed live news: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching news")

@router.post("/news/read", response_model=None)
async def mark_as_read(
        external_id: str = Body(..., embed=True),
        user: dict = Depends(get_current_user)
):
    try:
        user_id = getattr(user, "id", None) or user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        supabase_service.table("read_articles").upsert(
            {"user_id": user_id, "external_id": external_id},
            on_conflict="user_id,external_id"
        ).execute()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error marking as read: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while marking as read")

@router.post("/news/bookmark", response_model=None)
async def bookmark_article(
    article_data: dict,
    user: dict = Depends(get_current_user)
):
    try:
        user_id = getattr(user, "id", None) or user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Map raw RSS entry to DB article
        article = map_entry_to_article(article_data)
        external_id = article["external_id"]
        
        # Set audio_status='none' so the scheduler skips bookmarked-only articles.
        # ignore_duplicates=True means if the article already exists (via RSS ingest),
        # this INSERT is a no-op — preserving the existing audio_status.
        article["audio_status"] = "none"
        supabase_service.table("news_articles").upsert(
            [article], 
            on_conflict="external_id",
            ignore_duplicates=True
        ).execute()
        
        # Fetch the article ID (works whether it was just inserted or already existed)
        lookup = supabase_service.table("news_articles") \
            .select("id") \
            .eq("external_id", external_id) \
            .single() \
            .execute()
        
        if not lookup.data:
            raise Exception("Article not found after upsert")
            
        article_id = lookup.data["id"]
        
        # Create bookmark mapping
        supabase_service.table("bookmarks").upsert(
            [{"user_id": user_id, "article_id": article_id}],
            on_conflict="user_id,article_id"
        ).execute()
        
        return {"status": "success", "article_id": article_id}
    except Exception as e:
        logger.error(f"Error bookmarking article: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error while bookmarking: {e}")

@router.delete("/news/bookmark/{article_id_or_url:path}", response_model=None)
async def unbookmark_article(
    article_id_or_url: str,
    user: dict = Depends(get_current_user)
):
    """
    Remove a bookmark by either the internal UUID or the source URL.
    The :path modifier allows the article_id_or_url to contain slashes (URLs).
    """
    try:
        user_id = getattr(user, "id", None) or user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        target_article_id = article_id_or_url
        
        # 1. Identify if it's a UUID, Hash (external_id), or raw URL
        import re
        is_uuid = False
        try:
            import uuid
            uuid.UUID(article_id_or_url)
            is_uuid = True
        except (ValueError, TypeError):
            is_uuid = False
            
        is_hash = bool(re.match(r"^[a-fA-F0-9]{64}$", article_id_or_url))
        
        if not is_uuid:
            # Resolve the internal ID via external_id lookup
            if is_hash:
                # It's already our SHA256 external_id
                external_id = article_id_or_url.lower()
            else:
                # It's a raw source URL, hash it to get our external_id
                from src.services.rss.ingester import build_external_id
                external_id = build_external_id({"link": article_id_or_url})
        
            lookup = supabase_service.table("news_articles") \
                .select("id") \
                .eq("external_id", external_id) \
                .execute()
                
            if not lookup.data:
                # Article not found in our system, nothing to delete
                return {"status": "success", "message": "Article not found; no bookmark removed."}
                
            target_article_id = lookup.data[0]["id"]

        # 2. Delete the bookmark mapping
        supabase_service.table("bookmarks") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("article_id", target_article_id) \
            .execute()
            
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error unbookmarking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while unbookmarking")

@router.get("/news/bookmarks", response_model=None)
async def get_user_bookmarks(
    user: dict = Depends(get_current_user)
):
    try:
        user_id = getattr(user, "id", None) or user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Join bookmarks and news_articles
        response = supabase_service.table("bookmarks") \
            .select("news_articles(*)") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .execute()
            
        # Flatten and clean the result
        articles = [_clean_article(row["news_articles"]) for row in response.data if row.get("news_articles")]
        
        return {"count": len(articles), "articles": articles}
    except Exception as e:
        logger.error(f"Error fetching bookmarks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching bookmarks")

@router.put("/news/interests", response_model=None)
async def update_user_interests(
    interests: List[str] = Body(..., embed=True, description="List of interest categories, e.g. ['Startups', 'Finance', 'Technology', 'International']"),
    user: dict = Depends(get_current_user)
):
    """Update the authenticated user's interest preferences."""
    try:
        user_id = getattr(user, "id", None) or user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        supabase_service.table("users").update(
            {"interests": interests}
        ).eq("id", user_id).execute()
        
        return {"status": "success", "interests": interests}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating interests: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while updating interests")
