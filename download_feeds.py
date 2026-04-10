
import httpx
import os

def download_feeds():
    feeds = {
        "techcrunch": "https://techcrunch.com/category/startups/feed/",
        "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for name, url in feeds.items():
        try:
            print(f"Downloading {name}...")
            response = httpx.get(url, headers=headers, timeout=15)
            filename = f"{name}_feed_raw.xml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Saved to {filename} (Size: {len(response.text)})")
        except Exception as e:
            print(f"Error downloading {name}: {e}")

if __name__ == "__main__":
    download_feeds()
