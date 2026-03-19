from fastapi import FastAPI
from src.api.auth import router as auth_router

app = FastAPI(title="HyPot-News API")

# Include routers
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to HyPot-News API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
