import asyncio
import logging
import signal
import sys
from src.core.config import settings
from src.core.scheduler import scheduler
from src.jobs.news_fetch import run_news_fetch_job
from src.jobs.audio_jobs import run_audio_generation_job, run_temp_cleanup_job

# Configure logging for the worker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("hypot-worker")

async def start_worker():
    logger.info("🚀 Starting HyPot News Background Worker...")
    
    # Schedule RSS Fetch Job
    scheduler.add_job(
        run_news_fetch_job,
        trigger="interval",
        minutes=settings.RSS_FETCH_INTERVAL_MINUTES,
        id="rss_fetch_job",
        replace_existing=True,
    )
    
    # Schedule Audio Generation Job (Batched)
    scheduler.add_job(
        run_audio_generation_job,
        trigger="interval",
        minutes=20, 
        id="audio_generation_job",
        replace_existing=True,
    )
    
    # Schedule Temp Cleanup Job
    scheduler.add_job(
        run_temp_cleanup_job,
        trigger="interval",
        minutes=30,
        id="temp_cleanup_job",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Worker scheduler started.")
    logger.info(f"RSS Fetch: every {settings.RSS_FETCH_INTERVAL_MINUTES} min")
    logger.info("Audio Generation: every 1 min")
    
    # Handle graceful shutdown for asyncio
    loop = asyncio.get_running_loop()
    
    def shutdown_handler():
        logger.info("Shutting down worker...")
        scheduler.shutdown(wait=False)
        # Force exit after a short delay if needed, 
        # but in a simple worker like this, stopping the loop is usually enough
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown_handler)
        except NotImplementedError:
            # signal handlers are not implemented on Windows for asyncio
            pass

    # Keep the process alive using asyncio-friendly sleep
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker interrupted.")
    finally:
        if scheduler.running:
            scheduler.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(start_worker())
    except (KeyboardInterrupt, SystemExit):
        pass

