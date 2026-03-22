import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "")
    
    # RSS CRON JOB Settings
    RSS_FETCH_INTERVAL_MINUTES: int = int(os.getenv("RSS_FETCH_INTERVAL_MINUTES", "180"))

settings = Settings()
