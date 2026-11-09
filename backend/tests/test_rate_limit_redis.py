import os
import time
import uuid
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def redis_url():
    url = os.getenv("TEST_REDIS_URL") or os.getenv("REDIS_URL")
    if not url:
        pytest.skip("No TEST_REDIS_URL or REDIS_URL configured for Redis integration test")
    return url


def test_redis_rate_limit(redis_url, monkeypatch):
    from backend.app.config import settings
    import redis

    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 3)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 2)
    monkeypatch.setattr(settings, "REDIS_URL", redis_url)
    monkeypatch.setattr(settings, "REDIS_CONNECT_TIMEOUT_SECONDS", 1.0)
    monkeypatch.setattr(settings, "REDIS_RETRY_INTERVAL_SECONDS", 1.0)
    monkeypatch.setattr(settings, "RATE_LIMIT_KEY_PREFIX", f"test:rate-limit:{uuid.uuid4().hex}")

    from backend.app.middleware.rate_limit import RateLimitMiddleware, RedisBucket

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    probe_client = redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=1.0,
        socket_timeout=1.0,
    )
    try:
        probe_client.ping()
        with TestClient(app) as tc:
            for _ in range(3):
                assert tc.get("/ping").status_code == 200
            response = tc.get("/ping")
            assert response.status_code == 429
            middleware = app.middleware_stack
            found_redis_bucket = False
            while hasattr(middleware, "app"):
                if isinstance(middleware, RateLimitMiddleware):
                    assert isinstance(middleware.bucket, RedisBucket)
                    found_redis_bucket = True
                    break
                middleware = middleware.app
            assert found_redis_bucket

            time.sleep(2.1)
            assert tc.get("/ping").status_code == 200
    finally:
        probe_client.close()
