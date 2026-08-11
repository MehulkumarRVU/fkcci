from contextlib import asynccontextmanager
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_database
from app.routes import (
    auth_router,
    sessions_router,
    skills_router,
    analysis_router,
    analytics_router,
    gamification_router,
    reports_router,
    notes_router,
)
from app.middleware.rate_limit import RateLimitMiddleware
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()

    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 16:
        print("WARNING: SECRET_KEY is short or missing. Use a strong secret in production.")
        if os.getenv("ENV", "development") == "production":
            print("ERROR: In production, SECRET_KEY must be set to a strong value. Exiting.")
            sys.exit(1)

    if settings.ALGORITHM not in ("HS256", "HS384", "HS512"):
        print(f"WARNING: Unusual JWT algorithm configured: {settings.ALGORITHM}")

    print("[OK] Database initialized successfully")
    yield

    print("[OK] PocketCoach AI backend shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="PocketCoach AI API",
    description="AI-Powered Real-Time Sports Technique Coach for Table Tennis, Boxing & Badminton",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiting middleware early
app.add_middleware(RateLimitMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(skills_router)
app.include_router(analysis_router)
app.include_router(analytics_router)
app.include_router(gamification_router)
app.include_router(reports_router)
app.include_router(notes_router)

# Root endpoint
@app.get("/")
async def root():
    from app.sports_registry import get_supported_sport_types

    return {
        "message": "Welcome to PocketCoach AI API",
        "version": "1.0.0",
        "sports": get_supported_sport_types(),
        "docs": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "PocketCoach AI Backend",
        "port": 8080
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
