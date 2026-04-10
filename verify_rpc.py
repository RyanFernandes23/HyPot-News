
import httpx
import json
from datetime import datetime

# We will use the local server
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_endpoint(endpoint, params=None):
    print(f"\n--- Testing {endpoint} ---")
    try:
        # We need a token to pass get_current_user, but we want to avoid authentication logic
        # For local testing, we might need to mock get_current_user in the app itself
        # Or, since we're just verifying the DB query logic, we can just check if it returns 401 (meaning it reached the endpoint)
        # However, to REALLY verify the fix, we need to bypass auth.
        
        # Let's try to hit it with a dummy token and see the error.
        # If it's 401, it's working but auth blocked us.
        # If it's 500, then our RPC/Logic failed even before auth (unlikely) or after (if mocked).
        
        headers = {"Authorization": "Bearer dummy_token"}
        response = httpx.get(f"{BASE_URL}{endpoint}", params=params, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Count: {data.get('count')}")
            if data.get('articles'):
                print(f"First article headline: {data['articles'][0].get('headline')}")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with a category that usually has many articles
    test_endpoint("/news/live", params={"category": "International", "limit": 5})
    test_endpoint("/news/live", params={"category": "Startups", "limit": 5})
    test_endpoint("/news", params={"category": "Technology", "limit": 5})
