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
        response = supabase_service.table("news_articles") \
            .select("*") \
            .eq("category", category) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
            
        return {"category": category, "limit": limit, "count": len(response.data), "articles": response.data}
    except Exception as e:
        logger.error(f"Error fetching news for category '{category}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching news")
