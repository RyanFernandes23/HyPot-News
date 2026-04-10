import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # S3 Storage Settings
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "HyPot-News")
    AWS_S3_ENDPOINT_URL: str = os.getenv("AWS_S3_ENDPOINT_URL", "")

    # Audio Processing Settings
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp_audio")

    # RSS CRON JOB Settings
    RSS_FETCH_INTERVAL_MINUTES: int = int(os.getenv("RSS_FETCH_INTERVAL_MINUTES", "5"))
    MAX_AUDIO_TASKS_PER_CATEGORY: int = int(
        os.getenv("MAX_AUDIO_TASKS_PER_CATEGORY", "3")
    )

    # Briefing Schedule (UTC) - Audio prep runs after GNews fetch (3am)
    BRIEFING_SCHEDULE_HOUR: str = os.getenv("BRIEFING_SCHEDULE_HOUR", "4")
    BRIEFING_SCHEDULE_MINUTE: str = os.getenv("BRIEFING_SCHEDULE_MINUTE", "0")

    # Admin Settings
    ALLOW_DEV_CLEANUP: bool = os.getenv("ALLOW_DEV_CLEANUP", "false").lower() == "true"

    # GNews API Settings
    GNEWS_API_KEY: str = os.getenv("GNEWS_API_KEY", "")


settings = Settings()
