import sys
from fastapi.testclient import TestClient

try:
    from src.main import app
except Exception as e:
    print(f"Failed to import app: {e}")
    sys.exit(1)

client = TestClient(app)

print("Testing /api/v1/news API endpoint...")
try:
    response = client.get("/api/v1/news?category=International&limit=3")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Category: {data.get('category')}")
        print(f"Limit: {data.get('limit')}")
        print(f"Count returned: {data.get('count')}")
        print("First article headline:", data['articles'][0]['headline'] if data['articles'] else "None")
    else:
        print(response.text)
except Exception as e:
    print(f"Test failed: {e}")
