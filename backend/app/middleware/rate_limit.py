import asyncio
import logging
import time
import inspect
from typing import Dict, Optional

from redis.exceptions import RedisError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from ..config import settings

logger = logging.getLogger(__name__)

_INCREMENT_WITH_EXPIRY = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


class InMemoryBucket:
    def __init__(self, max_requests: int, window: int):
        self.max = max_requests
        self.window = window
        self.hits: Dict[str, list[float]] = {}
        self.lock = asyncio.Lock()

    async def hit(self, key: str) -> tuple[bool, int]:
        now = time.time()
        async with self.lock:
            timestamps = [timestamp for timestamp in self.hits.get(key, []) if timestamp > now - self.window]
            timestamps.append(now)
            self.hits[key] = timestamps
            remaining = max(0, self.max - len(timestamps))
            return len(timestamps) <= self.max, remaining


class RedisBucket:
    def __init__(self, redis_client, max_requests: int, window: int):
        self.redis = redis_client
        self.max = max_requests
        self.window = window

    async def hit(self, key: str) -> tuple[bool, int]:
        count = await self.redis.eval(_INCREMENT_WITH_EXPIRY, 1, key, self.window)
        allowed = count <= self.max
        return allowed, max(0, self.max - count)


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        self.requests = settings.RATE_LIMIT_REQUESTS
        self.window = settings.RATE_LIMIT_WINDOW_SECONDS
        self.redis_url = settings.REDIS_URL
        self.connect_timeout = settings.REDIS_CONNECT_TIMEOUT_SECONDS
        self.retry_interval = settings.REDIS_RETRY_INTERVAL_SECONDS
        self.bucket: InMemoryBucket | RedisBucket = InMemoryBucket(self.requests, self.window)
        self.redis_client = None
        self._redis_retry_after = 0.0
        self._redis_lock = asyncio.Lock()
        self._key_prefix = f"{settings.RATE_LIMIT_KEY_PREFIX}:"

    async def _close_redis(self) -> None:
        client, self.redis_client = self.redis_client, None
        if client is None:
            return
        close = getattr(client, "aclose", None) or getattr(client, "close", None)
        if close:
            result = close()
            if inspect.isawaitable(result):
                await result

    async def _get_bucket(self) -> InMemoryBucket | RedisBucket:
        if isinstance(self.bucket, RedisBucket) or not self.redis_url:
            return self.bucket

        if time.monotonic() < self._redis_retry_after:
            return self.bucket

        async with self._redis_lock:
            if isinstance(self.bucket, RedisBucket):
                return self.bucket
            if time.monotonic() < self._redis_retry_after:
                return self.bucket
            client = None
            connected = False
            try:
                import redis.asyncio as aioredis

                client = aioredis.from_url(
                    self.redis_url,
                    socket_connect_timeout=self.connect_timeout,
                    socket_timeout=self.connect_timeout,
                )
                self.redis_client = client
                await client.ping()
                connected = True
            except ImportError:
                logger.warning("Redis package is unavailable; using in-memory rate limiting")
            except (RedisError, OSError, TimeoutError):
                logger.warning("Redis is unavailable; using in-memory rate limiting")
                if client is not None:
                    try:
                        await self._close_redis()
                    except RedisError:
                        logger.warning("Failed to close unavailable Redis connection")
            if connected and client is not None:
                self.bucket = RedisBucket(client, self.requests, self.window)
                logger.info("Redis-backed rate limiting is active")
                return self.bucket
            self.redis_client = None
            self._redis_retry_after = time.monotonic() + self.retry_interval
            return self.bucket

    async def _hit(self, key: str) -> tuple[bool, int]:
        bucket = await self._get_bucket()
        if isinstance(bucket, RedisBucket):
            try:
                return await bucket.hit(key)
            except RedisError:
                logger.warning("Redis rate limiting failed; falling back to in-memory rate limiting", exc_info=True)
                await self._close_redis()
                self.bucket = InMemoryBucket(self.requests, self.window)
                self._redis_retry_after = time.monotonic() + self.retry_interval
                return await self.bucket.hit(key)
        return await bucket.hit(key)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            async def close_on_shutdown(message):
                await send(message)
                if message["type"] == "lifespan.shutdown.complete":
                    await self._close_redis()

            await self.app(scope, receive, close_on_shutdown)
            return

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        ip = request.client.host if request.client else "unknown"
        allowed, _ = await self._hit(f"{self._key_prefix}{ip}")
        if not allowed:
            response = JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(self.window)},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
