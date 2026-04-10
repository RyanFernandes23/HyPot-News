
import httpx

def ping():
    urls = ["http://127.0.0.1:8000/health", "http://0.0.0.0:8000/health", "http://localhost:8000/health"]
    for url in urls:
        print(f"Pinging {url}...")
        try:
            response = httpx.get(url, timeout=5)
            print(f"Success! Status: {response.status_code}, Body: {response.text}")
            return url
        except Exception as e:
            print(f"Failed: {e}")
    return None

if __name__ == "__main__":
    ping()
