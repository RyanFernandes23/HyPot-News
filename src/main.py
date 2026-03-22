from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

from src.api.auth import router as auth_router
from src.api.news import router as news_router
from src.core.config import settings
from src.core.scheduler import scheduler
from src.jobs.news_fetch import run_news_fetch_job

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Schedule and start background jobs
    scheduler.add_job(
        run_news_fetch_job,
        trigger="interval",
        minutes=settings.RSS_FETCH_INTERVAL_MINUTES,
        id="rss_fetch_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"[Scheduler] RSS fetch job scheduled every {settings.RSS_FETCH_INTERVAL_MINUTES} minutes.")
    
    yield
    
    # Shutdown: Stop jobs gracefully
    scheduler.shutdown(wait=False)
    logger.info("[Scheduler] Shut down successfully.")

app = FastAPI(title="HyPot-News API", lifespan=lifespan)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to HyPot-News API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
