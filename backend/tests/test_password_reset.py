import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal
from app.models.athlete import Athlete
from app.models.password_reset_token import PasswordResetToken
from app.services.auth_service import AuthService
from app.services.email_service import send_password_reset_email

client = TestClient(app)


def _signup(username):
    client.post(
        "/api/auth/signup",
        json={
            "email": f"{username}@example.com",
            "username": username,
            "password": "originalpass123",
            "sport_type": "boxing",
            "skill_level": "beginner",
        },
    )


def _get_reset_token_for(username):
    with SessionLocal() as db:
        athlete = db.query(Athlete).filter(Athlete.username == username).first()
        auth_service = AuthService(db)
        return auth_service.create_password_reset_token(athlete), athlete.id


def test_request_returns_generic_message_for_existing_email():
    _signup("reset_athlete_1")
    resp = client.post("/api/auth/password-reset/request", json={"email": "reset_athlete_1@example.com"})
    assert resp.status_code == 200
    assert "sent" in resp.json()["message"].lower()


def test_request_survives_smtp_failure_without_500():
    """A misconfigured/rejected SMTP send (bad credentials, network error,
    etc.) must not crash the request or reveal to the caller that sending
    failed - the reset token is still created, and an admin finds out via
    the server-side log instead."""
    _signup("reset_athlete_smtp")
    with patch("app.routes.auth.send_password_reset_email", side_effect=Exception("SMTP down")):
        resp = client.post("/api/auth/password-reset/request", json={"email": "reset_athlete_smtp@example.com"})
    assert resp.status_code == 200
    assert "sent" in resp.json()["message"].lower()


def test_unconfigured_smtp_does_not_log_password_reset_link(caplog):
    with patch("app.services.email_service.settings.SMTP_HOST", None):
        send_password_reset_email("private@example.com", "https://example.test/reset?token=secret-token")

    assert "secret-token" not in caplog.text
    assert "private@example.com" not in caplog.text


def test_request_returns_same_generic_message_for_unknown_email():
    resp = client.post("/api/auth/password-reset/request", json={"email": "definitely_not_registered@example.com"})
    assert resp.status_code == 200
    assert "sent" in resp.json()["message"].lower()


def test_confirm_resets_password_and_old_password_stops_working():
    _signup("reset_athlete_2")
    token, _ = _get_reset_token_for("reset_athlete_2")

    confirm_resp = client.post(
        "/api/auth/password-reset/confirm", json={"token": token, "new_password": "brandnewpass456"}
    )
    assert confirm_resp.status_code == 200, confirm_resp.text

    old_login = client.post("/api/auth/login", data={"username": "reset_athlete_2", "password": "originalpass123"})
    assert old_login.status_code == 401

    new_login = client.post("/api/auth/login", data={"username": "reset_athlete_2", "password": "brandnewpass456"})
    assert new_login.status_code == 200


def test_token_is_single_use():
    _signup("reset_athlete_3")
    token, _ = _get_reset_token_for("reset_athlete_3")

    first = client.post("/api/auth/password-reset/confirm", json={"token": token, "new_password": "newpass789012"})
    assert first.status_code == 200

    second = client.post("/api/auth/password-reset/confirm", json={"token": token, "new_password": "anotherpass345"})
    assert second.status_code == 400


def test_expired_token_rejected():
    _signup("reset_athlete_4")
    token, athlete_id = _get_reset_token_for("reset_athlete_4")

    with SessionLocal() as db:
        prt = db.query(PasswordResetToken).filter(PasswordResetToken.athlete_id == athlete_id).first()
        prt.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    resp = client.post("/api/auth/password-reset/confirm", json={"token": token, "new_password": "newpassexp123"})
    assert resp.status_code == 400


def test_invalid_token_rejected():
    resp = client.post(
        "/api/auth/password-reset/confirm", json={"token": "not-a-real-token", "new_password": "newpass99999"}
    )
    assert resp.status_code == 400


def test_short_new_password_rejected():
    _signup("reset_athlete_5")
    token, _ = _get_reset_token_for("reset_athlete_5")

    resp = client.post("/api/auth/password-reset/confirm", json={"token": token, "new_password": "abc"})
    assert resp.status_code == 400


def test_reset_revokes_existing_refresh_tokens():
    _signup("reset_athlete_6")
    login_resp = client.post("/api/auth/login", data={"username": "reset_athlete_6", "password": "originalpass123"})
    refresh_token = login_resp.json()["refresh_token"]

    token, _ = _get_reset_token_for("reset_athlete_6")
    client.post("/api/auth/password-reset/confirm", json={"token": token, "new_password": "resetpass123456"})

    refresh_resp = client.post("/api/auth/token/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 401
