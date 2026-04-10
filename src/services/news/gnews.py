import logging
from typing import List, Dict, Any, Optional
import httpx
from src.core.config import settings

logger = logging.getLogger(__name__)

GNEWS_BASE_URL = "https://gnews.io/api/v4"

CATEGORIES = ["world", "business", "technology", "science"]


def get_category_for_briefing(cat: str) -> str:
    """Map user category to GNews API category."""
    mapping = {
        "international": "world",
        "finance": "business",
        "technology": "technology",
        "startups": "technology",
        "science": "science",
    }
    return mapping.get(cat.lower(), "world")


async def fetch_gnews_articles(
    category: str = "world",
    lang: str = "en",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """Fetch articles from GNews API for a specific category."""
    if not settings.GNEWS_API_KEY:
        logger.error("GNEWS_API_KEY not configured")
        return []

    gnews_category = get_category_for_briefing(category)

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                f"{GNEWS_BASE_URL}/top-headlines",
                params={
                    "category": gnews_category,
                    "lang": lang,
                    "max": max_results,
                },
                headers={"Authorization": settings.GNEWS_API_KEY},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            articles = data.get("articles", [])
            logger.info(
                f"Fetched {len(articles)} articles from GNews ({category}/{gnews_category})"
            )
            return articles

    except Exception as e:
        logger.error(f"Failed to fetch from GNews ({category}): {e}")
        return []


def map_gnews_to_article(
    gnews_article: Dict[str, Any],
    category: str,
    briefing_date: str,
) -> Dict[str, Any]:
    """Map GNews article to daily_briefing_articles table schema."""
    source = gnews_article.get("source", {})

    return {
        "external_id": gnews_article.get("id", ""),
        "headline": gnews_article.get("title", ""),
        "description": gnews_article.get("description", ""),
        "url": gnews_article.get("url", ""),
        "url_to_image": gnews_article.get("image", ""),
        "source_id": source.get("id", ""),
        "source_name": source.get("name", ""),
        "published_at": gnews_article.get("publishedAt", ""),
        "briefing_date": briefing_date,
        "category": category,
    }


async def fetch_and_ingest_daily_briefing() -> int:
    """Fetch GNews for all categories and ingest into daily_briefing_articles."""
    from src.db.supabase import supabase_service
    from src.services.storage.s3 import s3_service as s3
    from datetime import datetime

    briefing_date = datetime.utcnow().date().isoformat()
    categories = ["world", "business", "technology", "science"]
    total_ingested = 0

    # Cleanup old articles and S3 audio files before fetching new ones
    try:
        # Delete old articles (briefing_date != today)
        delete_response = (
            supabase_service.table("daily_briefing_articles")
            .delete()
            .neq("briefing_date", briefing_date)
            .execute()
        )
        logger.info(
            f"Deleted {len(delete_response.data) if delete_response.data else 0} old briefing articles"
        )
    except Exception as cleanup_err:
        logger.warning(f"DB cleanup failed: {cleanup_err}")

    try:
        # Clean up S3 audio files (daily_briefing/ prefix)
        objects_to_delete = []
        paginator = s3.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=s3.bucket_name, Prefix="daily_briefing/")

        for page in pages:
            for obj in page.get("Contents", []):
                objects_to_delete.append({"Key": obj.get("Key", "")})

        if objects_to_delete:
            s3.s3_client.delete_objects(
                Bucket=s3.bucket_name,
                Delete={"Objects": objects_to_delete, "Quiet": True},
            )
            logger.info(f"Cleaned up {len(objects_to_delete)} old S3 audio files")
    except Exception as s3_err:
        logger.warning(f"S3 cleanup failed: {s3_err}")

    for category in categories:
        articles = await fetch_gnews_articles(
            category=category,
            max_results=10,
        )

        if not articles:
            logger.warning(f"No articles fetched for {category}, skipping")
            continue

        for article_data in articles:
            article = map_gnews_to_article(article_data, category, briefing_date)

            try:
                response = (
                    supabase_service.table("daily_briefing_articles")
                    .upsert(
                        article,
                        on_conflict="external_id",
                    )
                    .execute()
                )

                if response.data:
                    total_ingested += 1

            except Exception as e:
                logger.error(
                    f"Failed to ingest article {article.get('headline', '')}: {e}"
                )

    logger.info(f"Daily briefing ingested: {total_ingested} articles")
    return total_ingested
