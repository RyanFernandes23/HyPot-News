
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.rss.fetcher import fetch_feed

async def test():
    feed = {'url': 'http://feeds.bbci.co.uk/news/world/rss.xml', 'source': 'BBC News', 'category': 'International'}
    print(f"Testing fetch for: {feed['url']}")
    entries = await fetch_feed(feed)
    print(f"Fetched {len(entries)} entries")

if __name__ == "__main__":
    asyncio.run(test())
