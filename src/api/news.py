from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from src.db.supabase import supabase_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/news", response_model=None)
async def get_news_by_category(
    category: str = Query(..., description="The category of news to fetch, e.g., 'Tech', 'Finance'"),
    limit: int = Query(10, ge=1, le=100, description="Number of top articles to fetch")
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
