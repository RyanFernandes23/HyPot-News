from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

from src.api.auth import router as auth_router
from src.api.news import router as news_router
from src.api.audio import router as audio_router
from src.api.admin import router as admin_router
from src.core.config import settings
from src.core.scheduler import scheduler
from src.jobs.news_fetch import run_news_fetch_job
from src.jobs.audio_jobs import run_briefing_audio_prep, run_temp_cleanup_job

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI service starting up...")

    # --- Schedule RSS Fetch Job ---
    scheduler.add_job(
        run_news_fetch_job,
        trigger="interval",
        minutes=settings.RSS_FETCH_INTERVAL_MINUTES,
        id="rss_fetch_job",
        replace_existing=True,
    )

    # --- Schedule Temp Audio Cleanup ---
    scheduler.add_job(
        run_temp_cleanup_job,
        trigger="interval",
        minutes=30,
        id="temp_cleanup_job",
        replace_existing=True,
    )

    # --- Schedule Daily Briefing Audio Prep (1:30 UTC & 13:30 UTC → ~7 AM/PM IST) ---
    scheduler.add_job(
        run_briefing_audio_prep,
        trigger="cron",
        hour="1,13",
        minute=30,
        id="daily_briefing_prep",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"Scheduler started — RSS every {settings.RSS_FETCH_INTERVAL_MINUTES}min, Briefing prep at 01:30 & 13:30 UTC")

    yield

    logger.info("FastAPI service shutting down...")
    if scheduler.running:
        scheduler.shutdown(wait=False)

app = FastAPI(title="HyPot-News API", lifespan=lifespan)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(audio_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to HyPot-News API (index.html not found)"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
