import asyncio
import threading

import pytest

import app.services.auth_service as auth_service_module
from backend.app.models.athlete import Athlete
from app.services.auth_service import AuthService, PasswordHashCapacityExceeded


def test_async_password_hashing_preserves_the_pbkdf2_format():
    auth_service = AuthService()
    hashed_password = asyncio.run(auth_service.get_password_hash_async("CorrectHorseBattery!"))

    assert hashed_password.startswith("pbkdf2_sha256$100000$")
    assert asyncio.run(
        auth_service.verify_password_async("CorrectHorseBattery!", hashed_password)
    )
    assert not asyncio.run(
        auth_service.verify_password_async("incorrect", hashed_password)
    )


def test_password_hashing_does_not_block_the_event_loop(monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def blocked_hash(_service, _password):
        started.set()
        if not release.wait(timeout=2):
            raise TimeoutError("Test hash operation was not released")
        return "test-hash"

    monkeypatch.setattr(AuthService, "get_password_hash", blocked_hash)

    async def verify_responsiveness():
        task = asyncio.create_task(AuthService().get_password_hash_async("password"))
        try:
            assert await asyncio.to_thread(started.wait, timeout=1)
            await asyncio.sleep(0.01)
            assert not task.done()
        finally:
            release.set()
        return await task

    assert asyncio.run(verify_responsiveness()) == "test-hash"


def test_cancelled_password_hash_request_releases_capacity_after_completion(
    monkeypatch,
):
    started = threading.Event()
    release = threading.Event()
    capacity = threading.BoundedSemaphore(1)

    def blocked_hash(_service, _password):
        started.set()
        if not release.wait(timeout=2):
            raise TimeoutError("Test hash operation was not released")
        return "test-hash"

    monkeypatch.setattr(AuthService, "get_password_hash", blocked_hash)
    monkeypatch.setattr(auth_service_module, "_password_hash_capacity", capacity)

    async def verify_cancellation():
        task = asyncio.create_task(AuthService().get_password_hash_async("password"))
        try:
            assert await asyncio.to_thread(started.wait, timeout=1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert not capacity.acquire(blocking=False)
        finally:
            release.set()

        assert await asyncio.to_thread(capacity.acquire, True, 1)
        capacity.release()

    asyncio.run(verify_cancellation())


def test_hash_queue_capacity_is_enforced(monkeypatch):
    monkeypatch.setattr(
        auth_service_module,
        "_password_hash_capacity",
        threading.BoundedSemaphore(0),
    )

    with pytest.raises(PasswordHashCapacityExceeded):
        asyncio.run(AuthService().get_password_hash_async("password"))


def test_signup_returns_retryable_overload_when_hash_queue_is_full(
    client,
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        auth_service_module,
        "_password_hash_capacity",
        threading.BoundedSemaphore(0),
    )

    response = client.post(
        "/api/auth/signup",
        json={
            "email": "hash-capacity@example.com",
            "username": "hash_capacity_user",
            "password": "CorrectHorseBattery!",
            "sport_type": "boxing",
        },
    )

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "1"
    assert (
        db_session.query(Athlete)
        .filter(Athlete.username == "hash_capacity_user")
        .first()
        is None
    )
