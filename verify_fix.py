import sys
import os
import logging
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath("c:/Users/Hp/OneDrive/Desktop/SandboxClub/HyPot-News"))

from src.main import app
from src.api.deps import get_current_user

# Setup logging
logging.basicConfig(level=logging.INFO)

# Mocked users
mock_user_no_interests = {"id": "user-no-interests"}
mock_user_with_interests = {"id": "user-with-interests"}

async def override_get_current_user():
    return mock_user_no_interests

app.dependency_overrides[get_current_user] = override_get_current_user

# We need to mock the supabase call in news.py as well
from src.api.news import supabase_service

original_execute = supabase_service.table("users").select("interests").eq("id", "user-no-interests").single().execute

def mock_execute(*args, **kwargs):
    # Simulate a user with null interests
    mock_resp = MagicMock()
    mock_resp.data = {"interests": None}
    return mock_resp

client = TestClient(app)

def test_for_you_null_interests():
    print("\n--- Testing /api/v1/news/live?category=for you with NULL interests ---")
    
    # Mock the specific call for user interests
    with MagicMock() as mock_table:
        with MagicMock() as mock_select:
            with MagicMock() as mock_eq:
                with MagicMock() as mock_single:
                    mock_single.execute.return_value = MagicMock(data={"interests": None})
                    mock_eq.single.return_value = mock_single
                    mock_select.eq.return_value = mock_eq
                    mock_table.select.return_value = mock_select
                    
                    # We need to patch the table call on the service
                    original_table = supabase_service.table
                    supabase_service.table = lambda name: mock_table if name == "users" else original_table(name)
                    
                    try:
                        response = client.get("/api/v1/news/live?category=for you")
                        print(f"Status Code: {response.status_code}")
                        if response.status_code == 200:
                            print("Success! Handled NULL interests.")
                        else:
                            print(f"Failed! Status: {response.status_code}, Response: {response.text}")
                    finally:
                        supabase_service.table = original_table

def test_fixed_category():
    print("\n--- Testing /api/v1/news/live?category=Finance (Fixed Category) ---")
    response = client.get("/api/v1/news/live?category=Finance&limit=1")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Basic category works.")
    else:
        print(f"Failed! Status: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    test_fixed_category()
    test_for_you_null_interests()
