"""Temporary runtime instrumentation for isolated Phase 2 profiling only."""

import asyncio
from collections import defaultdict, deque
import gc
import json
import math
import threading
import time

import anyio.to_thread
from fastapi.responses import JSONResponse
from sqlalchemy import event

from app.database import engine
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.auth_service import AuthService
from main import app as application


password_executor = getattr(
    __import__("app.services.auth_service", fromlist=["_password_hash_executor"]),
    "_password_hash_executor",
    None,
)
_lock = threading.Lock()
_loop_lags_ms = deque(maxlen=200_000)
_pool_wait_ms = deque(maxlen=200_000)
_sql_ms = defaultdict(lambda: deque(maxlen=200_000))
_rate_limit_ms = defaultdict(lambda: deque(maxlen=200_000))
_password_ms = defaultdict(lambda: deque(maxlen=200_000))
_hash_active = 0
_loop_task = None
_gc_baseline = gc.get_stats()
_password_queue_max = 0


def _append(target, key, value):
    with _lock:
        target[key].append(value)


def _percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return round(ordered[index], 3)


def _distribution(values):
    return {
        "samples": len(values),
        "p50_ms": _percentile(values, 0.50),
        "p95_ms": _percentile(values, 0.95),
        "p99_ms": _percentile(values, 0.99),
        "max_ms": round(max(values), 3) if values else None,
        "over_10ms": sum(value > 10 for value in values),
        "over_50ms": sum(value > 50 for value in values),
        "over_100ms": sum(value > 100 for value in values),
    }


async def _sample_event_loop():
    loop = asyncio.get_running_loop()
    interval = 0.01
    deadline = loop.time() + interval
    while True:
        await asyncio.sleep(max(0, deadline - loop.time()))
        now = loop.time()
        with _lock:
            _loop_lags_ms.append(max(0.0, (now - deadline) * 1000))
        deadline = max(deadline + interval, now + interval)


def _snapshot():
    with _lock:
        loop_values = list(_loop_lags_ms)
        pool_values = list(_pool_wait_ms)
        sql_values = {key: list(values) for key, values in _sql_ms.items()}
        rate_values = {key: list(values) for key, values in _rate_limit_ms.items()}
        password_values = {key: list(values) for key, values in _password_ms.items()}

    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter_stats = limiter.statistics()
    pool = engine.pool
    thread_metrics = {
        "active_process_threads": threading.active_count(),
        "anyio_default_total_tokens": limiter_stats.total_tokens,
        "anyio_default_borrowed_tokens": limiter_stats.borrowed_tokens,
        "anyio_default_tasks_waiting": limiter_stats.tasks_waiting,
        "password_operations_active": _hash_active,
    }
    if password_executor is not None:
        work_queue = getattr(password_executor, "_work_queue", None)
        thread_metrics["password_executor_queue_max"] = _password_queue_max
        thread_metrics.update(
            {
                "password_executor_workers": getattr(
                    password_executor, "_max_workers", None
                ),
                "password_executor_queued": (
                    work_queue.qsize() if work_queue is not None else None
                ),
            }
        )

    return {
        "event_loop_lag": _distribution(loop_values),
        "sqlalchemy_pool_wait": _distribution(pool_values),
        "sql_execution_by_statement": {
            key: _distribution(values) for key, values in sorted(sql_values.items())
        },
        "rate_limit_path": {
            key: _distribution(values) for key, values in sorted(rate_values.items())
        },
        "password_operation_wall_time": {
            key: _distribution(values)
            for key, values in sorted(password_values.items())
        },
        "threads": thread_metrics,
        "postgres_pool": {
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "status": pool.status(),
        },
        "gc": [
            {
                key: stats[key] - _gc_baseline[index][key]
                for key in ("collections", "collected", "uncollectable")
            }
            for index, stats in enumerate(gc.get_stats())
        ],
    }


def _clear():
    global _gc_baseline, _password_queue_max
    with _lock:
        _loop_lags_ms.clear()
        _pool_wait_ms.clear()
        _sql_ms.clear()
        _rate_limit_ms.clear()
        _password_ms.clear()
        _password_queue_max = 0
        _gc_baseline = gc.get_stats()


_original_do_get = engine.pool._do_get


def _timed_do_get():
    started = time.perf_counter()
    try:
        return _original_do_get()
    finally:
        _pool_wait_ms.append((time.perf_counter() - started) * 1000)


engine.pool._do_get = _timed_do_get


@event.listens_for(engine, "before_cursor_execute")
def _before_cursor_execute(connection, cursor, statement, parameters, context, executemany):
    context._phase2_sql_started = time.perf_counter()


@event.listens_for(engine, "after_cursor_execute")
def _after_cursor_execute(connection, cursor, statement, parameters, context, executemany):
    started = getattr(context, "_phase2_sql_started", None)
    if started is None:
        return
    operation = statement.lstrip().split(None, 1)[0].upper() if statement.strip() else "OTHER"
    _append(_sql_ms, operation, (time.perf_counter() - started) * 1000)


_original_rate_hit = RateLimitMiddleware._hit


async def _timed_rate_hit(self, key):
    started = time.perf_counter()
    try:
        return await _original_rate_hit(self, key)
    finally:
        path = "redis" if self.bucket.__class__.__name__ == "RedisBucket" else "memory"
        _append(_rate_limit_ms, path, (time.perf_counter() - started) * 1000)


RateLimitMiddleware._hit = _timed_rate_hit


_original_hash = AuthService.get_password_hash
_original_verify = AuthService.verify_password


def _timed_hash(self, password):
    global _hash_active
    _hash_active += 1
    started = time.perf_counter()
    try:
        return _original_hash(self, password)
    finally:
        _hash_active -= 1
        _append(_password_ms, "hash_computation", (time.perf_counter() - started) * 1000)


def _timed_verify(self, plain_password, hashed_password):
    global _hash_active
    _hash_active += 1
    started = time.perf_counter()
    try:
        return _original_verify(self, plain_password, hashed_password)
    finally:
        _hash_active -= 1
        _append(_password_ms, "verify_computation", (time.perf_counter() - started) * 1000)


AuthService.get_password_hash = _timed_hash
AuthService.verify_password = _timed_verify

if hasattr(AuthService, "get_password_hash_async"):
    _original_hash_async = AuthService.get_password_hash_async
    _original_verify_async = AuthService.verify_password_async

    async def _timed_hash_async(self, password):
        started = time.perf_counter()
        try:
            return await _original_hash_async(self, password)
        finally:
            _append(
                _password_ms,
                "hash_async_end_to_end",
                (time.perf_counter() - started) * 1000,
            )

    async def _timed_verify_async(self, plain_password, hashed_password):
        started = time.perf_counter()
        try:
            return await _original_verify_async(self, plain_password, hashed_password)
        finally:
            _append(
                _password_ms,
                "verify_async_end_to_end",
                (time.perf_counter() - started) * 1000,
            )

    AuthService.get_password_hash_async = _timed_hash_async
    AuthService.verify_password_async = _timed_verify_async

if password_executor is not None:
    _original_submit = password_executor.submit

    def _timed_submit(function, *args, **kwargs):
        global _password_queue_max
        submitted_at = time.perf_counter()

        def _run():
            _append(
                _password_ms,
                "executor_queue_wait",
                (time.perf_counter() - submitted_at) * 1000,
            )
            return function(*args, **kwargs)

        future = _original_submit(_run)
        work_queue = getattr(password_executor, "_work_queue", None)
        if work_queue is not None:
            with _lock:
                _password_queue_max = max(_password_queue_max, work_queue.qsize())
        return future

    password_executor.submit = _timed_submit


class Phase2Profiler:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        global _loop_task
        if scope["type"] == "http" and _loop_task is None:
            _loop_task = asyncio.create_task(_sample_event_loop())

        if scope["type"] == "http" and scope.get("path") == "/api/__phase2_profile":
            method = scope.get("method")
            if method == "POST":
                _clear()
                response = JSONResponse({"reset": True})
            elif method == "GET":
                response = JSONResponse(_snapshot())
            else:
                response = JSONResponse({"detail": "Method not allowed"}, status_code=405)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


app = Phase2Profiler(application)
