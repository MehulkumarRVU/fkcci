import time

import redis.asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError


def test_inmemory_rate_limit(monkeypatch):
    # Configure small window for fast tests
    from backend.app.config import settings

    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 3)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 1)
    monkeypatch.setattr(settings, "REDIS_URL", "")

    from backend.app.middleware.rate_limit import RateLimitMiddleware

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)

    # Allowed requests
    for _ in range(3):
        r = client.get("/ping")
        assert r.status_code == 200

    # Next should be rate limited
    r = client.get("/ping")
    assert r.status_code == 429

    # Wait for window to expire and ensure requests allowed again
    time.sleep(1.1)
    r = client.get("/ping")
    assert r.status_code == 200


def test_redis_unavailable_falls_back_to_in_memory(monkeypatch):
    from backend.app.config import settings
    from backend.app.middleware.rate_limit import InMemoryBucket, RateLimitMiddleware

    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:1/0")
    monkeypatch.setattr(settings, "REDIS_CONNECT_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(settings, "REDIS_RETRY_INTERVAL_SECONDS", 60)

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)

    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 429
    middleware = app.middleware_stack
    while hasattr(middleware, "app") and not isinstance(middleware, RateLimitMiddleware):
        middleware = middleware.app
    assert isinstance(middleware, RateLimitMiddleware)
    assert isinstance(middleware.bucket, InMemoryBucket)


def test_redis_connection_recovers_after_fallback(monkeypatch):
    from backend.app.config import settings
    from backend.app.middleware.rate_limit import RateLimitMiddleware, RedisBucket

    class FakeRedis:
        def __init__(self):
            self.available = False
            self.count = 0

        async def ping(self):
            if not self.available:
                raise ConnectionError("unavailable")

        async def eval(self, script, key_count, key, window):
            self.count += 1
            return self.count

        async def aclose(self):
            return None

    fake_redis = FakeRedis()
    monkeypatch.setattr(redis.asyncio, "from_url", lambda *args, **kwargs: fake_redis)
    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 10)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(settings, "REDIS_URL", "redis://test/0")
    monkeypatch.setattr(settings, "REDIS_CONNECT_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr(settings, "REDIS_RETRY_INTERVAL_SECONDS", 0.001)

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)

    assert client.get("/ping").status_code == 200
    time.sleep(0.01)
    fake_redis.available = True
    assert client.get("/ping").status_code == 200

    middleware = app.middleware_stack
    while hasattr(middleware, "app") and not isinstance(middleware, RateLimitMiddleware):
        middleware = middleware.app
    assert isinstance(middleware, RateLimitMiddleware)
    assert isinstance(middleware.bucket, RedisBucket)
    assert fake_redis.count == 1
