import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(method, path, params=None):
    print(f"Testing {method} {path}...")
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url)
        else:
            print(f"Unsupported method {method}")
            return False

        if response.status_code == 401:
            print(f"  [PASS] Got 401 Unauthorized as expected.")
            return True
        else:
            print(f"  [FAIL] Expected 401, but got {response.status_code}.")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"  [ERROR] Request failed: {e}")
        return False

def main():
    print("Verifying Authentication Protection (Unauthenticated Requests)")
    print("-" * 50)
    
    success = True
    
    # 1. News Endpoint
    success &= test_endpoint("GET", "/news", params={"category": "Tech"})
    
    # 2. Admin Endpoint
    success &= test_endpoint("POST", "/admin/dev-cleanup")
    
    # 3. Audio Proxy Endpoint (Random ID to test protection)
    success &= test_endpoint("GET", "/audio/test-article/headline/test.m3u8")
    
    print("-" * 50)
    if success:
        print("All tested endpoints are successfully protected by authentication (returned 401).")
    else:
        print("Some endpoints failed protection verification.")
        sys.exit(1)

if __name__ == "__main__":
    main()
