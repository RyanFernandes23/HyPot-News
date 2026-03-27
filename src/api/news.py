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

# Module-level cache for RSS feeds
# Structure: { "category": { "entries": [...], "fetched_at": timestamp } }
RSS_CACHE = {}

async def get_cached_feed(category: str) -> List[dict]:
    """
    Retrieves RSS entries for a category from cache if valid (60s),
    else fetches fresh from source.
    """
    now = time.time()
    cache_entry = RSS_CACHE.get(category)
    
    if cache_entry and (now - cache_entry["fetched_at"] < 60):
        logger.info(f"Using cached RSS feed for category: {category}")
        return cache_entry["entries"]
        
    # Cache miss or expired
    feed_descriptors = [f for f in RSS_FEEDS if f["category"] == category]
    if not feed_descriptors:
        return []
        
    all_entries = []
    for descriptor in feed_descriptors:
        try:
            entries = await fetch_feed(descriptor)
            all_entries.extend(entries)
        except Exception as e:
            logger.error(f"Error fetching feed in cache helper: {e}")
            
    if all_entries:
        RSS_CACHE[category] = {
            "entries": all_entries,
            "fetched_at": now
        }
        logger.info(f"Updated RSS cache for category: {category} ({len(all_entries)} entries)")
        
    return all_entries

@router.get("/news", response_model=None)
async def get_news_by_category(
    category: str = Query(..., description="The category of news to fetch, e.g., 'Tech', 'Finance'"),
    limit: int = Query(10, ge=1, le=100, description="Number of top articles to fetch"),
    user: dict = Depends(get_current_user)
):
    try:
        # Assuming table is 'news_articles' and we sort by newest 'created_at' or 'published_at'
        # Fallback to 'created_at' as that is Supabase default
        # Use selective columns to keep payload light.
        # Excludes: content, raw_data, headline_search_vector
        columns = (
            "id, external_id, source_name, author, headline, summarized_content, "
            "source_url, url_to_image, category, published_at, "
            "headline_hls_base_url, summary_hls_base_url, duration_seconds, audio_status"
        )
        
        response = supabase_service.table("news_articles") \
            .select(columns) \
            .eq("category", category) \
            .eq("audio_status", "ready") \
            .order("published_at", desc=True) \
            .limit(limit) \
            .execute()
            
        articles = response.data
        for article in articles:
            if article.get("headline_hls_base_url"):
                # Convert the stored path into a local proxy URL
                # Path format: articles/{id}/{type}/headline.m3u8
                path_parts = article["headline_hls_base_url"].split("/")
                if len(path_parts) >= 4:
                    article["headline_hls_base_url"] = f"/api/v1/audio/{path_parts[1]}/{path_parts[2]}/{path_parts[3]}"
            
            if article.get("summary_hls_base_url"):
                path_parts = article["summary_hls_base_url"].split("/")
                if len(path_parts) >= 4:
                    article["summary_hls_base_url"] = f"/api/v1/audio/{path_parts[1]}/{path_parts[2]}/{path_parts[3]}"
            
        return {"category": category, "limit": limit, "count": len(articles), "articles": articles}
    except Exception as e:
        logger.error(f"Error fetching news for category '{category}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching news")

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
        
        # Build query
        query = supabase_service.table("news_articles") \
            .select("id, external_id, source_name, author, headline, summarized_content, "
                    "source_url, url_to_image, category, published_at, "
                    "headline_hls_base_url, summary_hls_base_url, duration_seconds, audio_status") \
            .eq("audio_status", "ready")
        
        if final_interests:
            query = query.in_("category", final_interests)
            
        # Category-wise sorting: category ASC, published_at DESC
        response = query.order("category", desc=False) \
            .order("published_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
            
        articles = response.data
        for article in articles:
            # Proxy audio URLs (DRY: could be a helper function)
            for key in ["headline_hls_base_url", "summary_hls_base_url"]:
                if article.get(key):
                    parts = article[key].split("/")
                    if len(parts) >= 4:
                        article[key] = f"/api/v1/audio/{parts[1]}/{parts[2]}/{parts[3]}"
            
        return {
            "interests": final_interests,
            "limit": limit,
            "offset": offset,
            "count": len(articles),
            "articles": articles
        }
    except Exception as e:
        logger.error(f"Error fetching briefing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching briefing")

@router.get("/news/live", response_model=None)
async def get_live_news(
    category: str = Query(..., description="The category of news to fetch from live RSS feeds"),
    limit: int = Query(20, ge=1, le=50, description="Number of items to return"),
    before: Optional[str] = Query(None, description="ISO timestamp cursor for pagination"),
    user: dict = Depends(get_current_user)
):
    try:
        user_id = getattr(user, "id", None) or user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        # 1. Fetch from Cache or Source
        all_entries = await get_cached_feed(category)
        if not all_entries:
            raise HTTPException(status_code=404, detail=f"No news articles found for category '{category}'")
            
        # 2. Sort by publication date (descending)
        def get_date(entry):
            try:
                if "published_parsed" in entry and entry["published_parsed"]:
                    return datetime(*entry["published_parsed"][:6])
                return datetime.min
            except:
                return datetime.min

        all_entries.sort(key=get_date, reverse=True)

        # 3. Fetch read articles for filtering
        read_response = supabase_service.table("read_articles") \
            .select("external_id") \
            .eq("user_id", user_id) \
            .execute()
        read_ids = {row["external_id"] for row in read_response.data}

        # 4. Filter and Paginate
        filtered_entries = []
        before_dt = None
        if before:
            try:
                # Support common ISO formats
                before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
            except Exception as e:
                logger.warning(f"Invalid before timestamp '{before}': {e}")

        for entry in all_entries:
            ext_id = entry.get("id") or entry.get("link")
            if not ext_id or ext_id in read_ids:
                continue
                
            entry_dt = get_date(entry)
            if before_dt and entry_dt >= before_dt:
                continue
            
            filtered_entries.append(entry)
            if len(filtered_entries) >= limit:
                break
            
        # 5. Determine next_cursor
        next_cursor = None
        if filtered_entries:
            oldest_entry = filtered_entries[-1]
            oldest_dt = get_date(oldest_entry)
            if oldest_dt != datetime.min:
                next_cursor = oldest_dt.isoformat()
            
        return {
            "category": category, 
            "limit": limit,
            "before": before,
            "next_cursor": next_cursor,
            "count": len(filtered_entries), 
            "articles": filtered_entries
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching live news: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching live news")

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

@router.delete("/news/bookmark/{article_id}", response_model=None)
async def unbookmark_article(
    article_id: str,
    user: dict = Depends(get_current_user)
):
    try:
        user_id = getattr(user, "id", None) or user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        supabase_service.table("bookmarks") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("article_id", article_id) \
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
            .execute()
            
        # Flatten the result
        articles = [row["news_articles"] for row in response.data if row.get("news_articles")]
        
        return {"count": len(articles), "articles": articles}
    except Exception as e:
        logger.error(f"Error fetching bookmarks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching bookmarks")

@router.put("/news/interests", response_model=None)
async def update_user_interests(
    interests: List[str] = Body(..., embed=True, description="List of interest categories, e.g. ['Tech', 'Finance']"),
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
