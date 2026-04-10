
import httpx

def check_feed(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = httpx.get(url, headers=headers)
        print(f"URL: {url}")
        print(response.text[:2000])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_feed("https://techcrunch.com/category/startups/feed/")
    print("\n" + "="*50 + "\n")
    check_feed("https://www.cnbc.com/id/100003114/device/rss/rss.html")
