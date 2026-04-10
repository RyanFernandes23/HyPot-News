import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.abspath("c:/Users/Hp/OneDrive/Desktop/SandboxClub/HyPot-News"))

from src.db.supabase import supabase_service

def test_supabase_in():
    print("Testing Supabase .in_ with None...")
    try:
        # This will likely fail with a 400 or raise an exception if categories is None
        res = supabase_service.table("news_articles").select("id").in_("category", None).limit(1).execute()
        print("Success (None):", res.data)
    except Exception as e:
        print("Caught Exception (None):", e)

    print("\nTesting Supabase .in_ with empty list...")
    try:
        res = supabase_service.table("news_articles").select("id").in_("category", []).limit(1).execute()
        print("Success ([]):", res.data)
    except Exception as e:
        print("Caught Exception ([]):", e)

if __name__ == "__main__":
    test_supabase_in()
