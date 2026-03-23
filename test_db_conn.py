
import sys
from pathlib import Path
print("--- Starting Test Script ---")
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from sqlalchemy import create_engine, text
    from src.core.config import settings
    from src.db.supabase import supabase_service
    print("--- Imports Successful ---")
except Exception as e:
    print(f"--- Import Failure: {e} ---")
    sys.exit(1)

def test_conn():
    print(f"URL from settings: {settings.POSTGRES_URL[:50]}...")
    
    print("--- Testing SQLAlchemy ---")
    try:
        engine = create_engine(settings.POSTGRES_URL, connect_args={'connect_timeout': 10})
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1"))
            print(f"SQLAlchemy Success: {res.fetchone()}")
    except Exception as e:
        print(f"SQLAlchemy Failure: {e}")

    print("--- Testing Supabase Client ---")
    try:
        res = supabase_service.table("news_articles").select("id").limit(1).execute()
        print(f"Supabase Success: {res.data}")
    except Exception as e:
        print(f"Supabase Failure: {e}")

if __name__ == "__main__":
    test_conn()
    print("--- Test Script Finished ---")
