import time
from typing import List, Dict, Any

def build_external_id(entry: Dict[str, Any]) -> str:
    return "test_id"

def map_entry_to_article(entry: Dict[str, Any]) -> Dict[str, Any]:
    image_url = entry.get("url_to_image") or entry.get("imageUrl") or ""
    source_name = entry.get("descriptor_source") or entry.get("source_name") or "Unknown"
    headline = entry.get("title") or entry.get("headline") or "No Title"
    category = entry.get("descriptor_category") or entry.get("category") or "Uncategorized"
    source_url = entry.get("link") or entry.get("source_url") or entry.get("url") or None
    summary = entry.get("summary") or entry.get("summarized_content") or ""
    
    published_at = entry.get("published_at") or entry.get("published")
    
    if "published_parsed" in entry and entry["published_parsed"]:
        try:
            published_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry["published_parsed"])
        except:
            published_at = None
    
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

test_entries = [
    {"published_at": ""},
    {"published": ""},
    {"published_at": " ", "published": None},
    {"published_at": None, "published": ""},
    {"published_at": None, "published": None},
]

print("Testing map_entry_to_article logic...")
for i, entry in enumerate(test_entries):
    result = map_entry_to_article(entry)
    print(f"Test {i}: entry={entry} -> published_at={result['published_at']!r}")
