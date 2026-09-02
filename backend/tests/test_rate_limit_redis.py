import os
import time
import asyncio
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient


redis_url = os.getenv("TEST_REDIS_URL") or os.getenv("REDIS_URL")
if not redis_url:
    pytest.skip("No REDIS_URL configured for Redis integration test", allow_module_level=True)


def test_redis_rate_limit():
    # Configure small window for fast tests
    from backend.app.config import settings
    settings.RATE_LIMIT_REQUESTS = 3
    settings.RATE_LIMIT_WINDOW_SECONDS = 2
    settings.REDIS_URL = redis_url

    import redis.asyncio as aioredis

    # Ensure Redis is reachable
    client = aioredis.from_url(redis_url, decode_responses=True)
    asyncio.run(client.ping())
    asyncio.run(client.flushdb())

    from backend.app.middleware.rate_limit import RateLimitMiddleware

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    tc = TestClient(app)

    # Allowed requests
    for _ in range(3):
        r = tc.get("/ping")
        assert r.status_code == 200

    # Next should be rate limited
    r = tc.get("/ping")
    assert r.status_code == 429

    # Wait for window to expire and ensure requests allowed again
    time.sleep(2.1)
    r = tc.get("/ping")
    assert r.status_code == 200

    asyncio.run(client.flushdb())
    asyncio.run(client.close())
