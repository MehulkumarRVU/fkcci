from contextlib import asynccontextmanager
import json
import logging
import os
import sys
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
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
    coaches_router,
    adaptive_router,
)
from app.middleware.rate_limit import RateLimitMiddleware
from app.config import settings, validate_production_security
from app.database import engine

logger = logging.getLogger("pocketcoach.request")


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_security(settings)
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
app.include_router(coaches_router)
app.include_router(adaptive_router)

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


def _check_database_readiness() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@app.get("/health/ready")
async def readiness_check():
    database_status = "ok"
    try:
        await run_in_threadpool(_check_database_readiness)
    except SQLAlchemyError:
        database_status = "error"
        logger.exception("database readiness check failed")

    redis_status = "not_configured"
    if settings.REDIS_URL:
        redis_client = None
        try:
            import redis.asyncio as aioredis
            from redis.exceptions import RedisError

            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
                socket_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
            )
            await redis_client.ping()
            redis_status = "ok"
        except (RedisError, OSError, TimeoutError):
            redis_status = "error"
            logger.exception("redis readiness check failed")
        finally:
            if redis_client is not None:
                await redis_client.aclose()

    ready = database_status == "ok" and redis_status in ("ok", "not_configured")
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "not_ready",
            "database": database_status,
            "redis": redis_status,
        },
    )


@app.middleware("http")
async def request_correlation_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            json.dumps(
                {
                    "event": "request_failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
                separators=(",", ":"),
            )
        )
        raise

    response.headers["X-Request-ID"] = request_id
    logger.info(
        json.dumps(
            {
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            },
            separators=(",", ":"),
        )
    )
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
