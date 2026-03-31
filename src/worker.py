import asyncio
import logging
import signal
import sys
import time
from datetime import datetime
from src.core.config import settings
from src.core.scheduler import scheduler
from src.jobs.news_fetch import run_news_fetch_job
from src.jobs.audio_jobs import run_briefing_audio_prep, run_temp_cleanup_job

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
    
    # Schedule Temp Cleanup Job
    scheduler.add_job(
        run_temp_cleanup_job,
        trigger="interval",
        minutes=30,
        id="temp_cleanup_job",
        replace_existing=True,
    )
    
    # Schedule Daily Briefing Audio Prep (7:00 AM and 7:00 PM)
    # Using multiple hours in cron trigger. 
    # Note: Times are in UTC if not specified otherwise in scheduler.py
    scheduler.add_job(
        run_briefing_audio_prep,
        trigger="cron",
        hour="1,13", # Corresponds to ~6:30/7:30 AM/PM in IST (+5:30)
        minute=30,
        id="daily_briefing_prep",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Worker scheduler started.")
    logger.info(f"RSS Fetch: every {settings.RSS_FETCH_INTERVAL_MINUTES} min")
    logger.info("Daily Briefing Prep: Scheduled for Morning & Evening")
    logger.info("Dramatiq: listening for immediate audio tasks...")

    
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

    # Keep the process alive using asyncio-friendly sleep with a live timer
    start_time = time.time()
    logger.info("Worker is active. Live status below:")
    
    try:
        while True:
            now_ts = time.time()
            elapsed = now_ts - start_time
            hours, rem = divmod(elapsed, 3600)
            minutes, seconds = divmod(rem, 60)
            
            # Get next job status
            next_job_str = "None"
            jobs = scheduler.get_jobs()
            if jobs:
                # Filter jobs that have a scheduled next run time
                active_jobs = [j for j in jobs if j.next_run_time]
                if active_jobs:
                    soonest_job = min(active_jobs, key=lambda j: j.next_run_time)
                    # Calculate time remaining
                    now_dt = datetime.now(soonest_job.next_run_time.tzinfo)
                    delay = soonest_job.next_run_time - now_dt
                    
                    # Format countdown
                    total_seconds = int(delay.total_seconds())
                    if total_seconds > 0:
                        j_hours, j_rem = divmod(total_seconds, 3600)
                        j_mins, j_secs = divmod(j_rem, 60)
                        next_job_str = f"{soonest_job.id} in {j_hours:02}:{j_mins:02}:{j_secs:02}"
                    else:
                        next_job_str = f"{soonest_job.id} starting..."

            # Print status line using carriage return \r to stay on the same line, in green
            status_line = f"\r\033[92m[HyPot Worker] ⏱  Uptime: {int(hours):02}:{int(minutes):02}:{int(seconds):02} | 📡 Next: {next_job_str}   \033[0m"
            sys.stdout.write(status_line)
            sys.stdout.flush()


            
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.write("\n") # Move to next line on stop
        logger.info("Worker interrupted.")
    finally:
        if scheduler.running:
            scheduler.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(start_worker())
    except (KeyboardInterrupt, SystemExit):
        pass

