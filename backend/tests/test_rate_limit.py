from fastapi import FastAPI
from fastapi.testclient import TestClient
import time


def test_inmemory_rate_limit():
    # Configure small window for fast tests
    from backend.app.config import settings
    settings.RATE_LIMIT_REQUESTS = 3
    settings.RATE_LIMIT_WINDOW_SECONDS = 1
    settings.REDIS_URL = ""

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
