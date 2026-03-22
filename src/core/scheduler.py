from apscheduler.schedulers.asyncio import AsyncIOScheduler

# We want an AsyncIOScheduler for FastAPI integration
scheduler = AsyncIOScheduler(timezone="UTC")
