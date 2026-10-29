import time
import asyncio
from typing import Dict, Optional
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..config import settings


class InMemoryBucket:
    def __init__(self, max_requests: int, window: int):
        self.max = max_requests
        self.window = window
        self.hits: Dict[str, list[float]] = {}
        self.lock = asyncio.Lock()

    async def hit(self, key: str) -> (bool, int):
        now = time.time()
        async with self.lock:
            arr = self.hits.get(key, [])
            # remove old timestamps
            arr = [t for t in arr if t > now - self.window]
            arr.append(now)
            self.hits[key] = arr
            remaining = max(0, self.max - len(arr))
            allowed = len(arr) <= self.max
            return allowed, remaining


class RedisBucket:
    def __init__(self, redis_client, max_requests: int, window: int):
        self.redis = redis_client
        self.max = max_requests
        self.window = window

    async def hit(self, key: str) -> (bool, int):
        # Uses INCR and EXPIRE to count requests in window
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window)
        allowed = count <= self.max
        remaining = max(0, self.max - count)
        return allowed, remaining


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        self.requests = settings.RATE_LIMIT_REQUESTS
        self.window = settings.RATE_LIMIT_WINDOW_SECONDS
        self.redis_url = settings.REDIS_URL
        self.bucket: Optional[object] = None
        self._init_bucket_sync()

    def _init_bucket_sync(self):
        # Attempt to initialize Redis bucket if REDIS_URL available and redis is installed.
        if self.redis_url:
            try:
                import redis.asyncio as aioredis

                redis_client = aioredis.from_url(self.redis_url)
                ping = redis_client.ping()
                loop = None
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(ping)
                    self.bucket = RedisBucket(redis_client, self.requests, self.window)
                    return
                except Exception:
                    ping.close()
                finally:
                    if loop is not None:
                        loop.close()
                    try:
                        asyncio.set_event_loop(None)
                    except RuntimeError:
                        pass
            except Exception:
                pass

        # Default fallback to local in-memory rate limiter.
        self.bucket = InMemoryBucket(self.requests, self.window)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        # identify client by IP or Authorization header
        ip = request.client.host if request.client else "unknown"
        key = f"rl:{ip}"

        # If Redis bucket, ensure redis client is connected
        if isinstance(self.bucket, RedisBucket):
            allowed, remaining = await self.bucket.hit(key)
        else:
            allowed, remaining = await self.bucket.hit(key)

        if not allowed:
            body = {"detail": "Rate limit exceeded"}
            headers = {"Retry-After": str(self.window)}
            response = JSONResponse(body, status_code=429, headers=headers)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
