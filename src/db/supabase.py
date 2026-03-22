from supabase import create_client, Client
from src.core.config import settings

def get_supabase() -> Client:
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    return create_client(url, key)

def get_supabase_service() -> Client:
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    return create_client(url, key)

supabase: Client = get_supabase()
supabase_service: Client = get_supabase_service()
