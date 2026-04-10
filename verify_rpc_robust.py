
import asyncio
from unittest.mock import MagicMock, patch
import httpx
from src.main import app

# Mock user data
MOCK_USER = {"id": "d5367b66-70e6-429d-9c4c-70337c767414", "email": "test@example.com"}

async def test_news_rpc():
    print("\n--- Verifying RPC News Filtering ---")
    
    # We bypass auth by patching the dependency
    from src.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Test 1: get_live_news for a specific category
        print("\nTesting /api/v1/news/live?category=International")
        response = await client.get("/api/v1/news/live?category=International&limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Success! Found {response.json().get('count')} articles")
        else:
            print(f"Error: {response.text}")

        # Test 2: get_live_news "For You" (uses RPC with multiple categories)
        print("\nTesting /api/v1/news/live?category=For%20You")
        response = await client.get("/api/v1/news/live?category=For%20You&limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Success! Found {response.json().get('count')} articles")
        else:
            print(f"Error: {response.text}")

        # Test 3: get_news_by_category
        print("\nTesting /api/v1/news?category=Startups")
        response = await client.get("/api/v1/news?category=Startups&limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Success! Found {response.json().get('count')} articles")
        else:
            print(f"Error: {response.text}")

        # Test 4: get_daily_briefing (uses get_unread_briefing RPC)
        print("\nTesting /api/v1/news/briefing")
        response = await client.get("/api/v1/news/briefing?limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Success! Found {response.json().get('count')} articles")
        else:
            print(f"Error: {response.text}")

    # Clean up
    app.dependency_overrides.clear()

if __name__ == "__main__":
    asyncio.run(test_news_rpc())
