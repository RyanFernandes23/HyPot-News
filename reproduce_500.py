import sys
import os
import logging
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath("c:/Users/Hp/OneDrive/Desktop/SandboxClub/HyPot-News"))

from src.main import app
from src.api.deps import get_current_user

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)

# Mock user
mock_user = {"id": "test-user-id"}

async def override_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_live_news(category="Finance", limit=10, before=None):
    print(f"\n--- Testing /api/v1/news/live?category={category}&limit={limit}&before={before} ---")
    url = f"/api/v1/news/live?category={category}&limit={limit}"
    if before:
        url += f"&before={before}"
    
    response = client.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"Error Response: {response.text}")
    else:
        data = response.json()
        print(f"Success! Count: {data.get('count')}")
        if data.get('articles'):
            print(f"First article headline: {data['articles'][0]['headline']}")

if __name__ == "__main__":
    # Test cases
    test_live_news(category="Finance")
    test_live_news(category="for you")
    test_live_news(category="NonExistentCategory")
    test_live_news(category="Finance", before="invalid-timestamp")
