import json
import logging
from typing import List, Dict, Any
import httpx
import feedparser

from src.services.rss.feeds import RSS_FEEDS

logger = logging.getLogger(__name__)

async def fetch_feed(feed_descriptor: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Fetches and parses a single RSS feed.
    Enriches each entry with source_name and category from the descriptor.
    """
    url = feed_descriptor["url"]
    source = feed_descriptor["source"]
    category = feed_descriptor["category"]
    
    entries = []
    
    try:
        # Use a custom User-Agent to prevent getting blocked
        headers = {
            "User-Agent": "HyPotNewsBot/1.0 (https://hypot-news.example.com)"
        }
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            
            # Parse the RSS XML
            parsed = feedparser.parse(response.text)
            
            # Extract entries and enrich
            for entry in parsed.entries:
                entry_dict = dict(entry)
                entry_dict["descriptor_source"] = source
                entry_dict["descriptor_category"] = category
                entries.append(entry_dict)
                
            logger.info(f"Fetched {len(entries)} items from {source} ({url})")
            
    except Exception as e:
        logger.error(f"Failed to fetch feed {source} ({url}): {e}")
        
    return entries

async def fetch_all_feeds() -> List[Dict[str, Any]]:
    """
    Loops over all defined RSS feeds, fetches them, and aggregates the results.
    Writes the aggregated result to a debug JSON file for inspection.
    """
    all_entries = []
    
    for feed in RSS_FEEDS:
        entries = await fetch_feed(feed)
        all_entries.extend(entries)
        
    # Sort by published date descending
    def get_sort_key(entry):
        try:
            if "published_parsed" in entry and entry["published_parsed"]:
                return tuple(entry["published_parsed"])
        except Exception:
            pass
        return ()
        
    all_entries.sort(key=get_sort_key, reverse=True)
    
    # Keep only 5 per category
    filtered_entries = []
    category_counts = {}
    for entry in all_entries:
        cat = entry["descriptor_category"]
        count = category_counts.get(cat, 0)
        if count < 5:
            filtered_entries.append(entry)
            category_counts[cat] = count + 1

    all_entries = filtered_entries
    logger.info(f"Total RSS items fetched (after limiting 5 per category): {len(all_entries)}")
    
    # Write to debug file
    try:
        with open("rss_debug_output.json", "w", encoding="utf-8") as f:
            json.dump(all_entries, f, indent=2, ensure_ascii=False)
        logger.info("Wrote raw RSS feed data to rss_debug_output.json")
    except Exception as e:
        logger.error(f"Failed to write debug output: {e}")
        
    return all_entries
