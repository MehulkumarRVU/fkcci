import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _signup_and_login(username):
    client.post(
        "/api/auth/signup",
        json={
            "email": f"{username}@example.com",
            "username": username,
            "password": "testpass123",
            "sport_type": "boxing",
            "skill_level": "beginner",
        },
    )
    login_resp = client.post("/api/auth/login", data={"username": username, "password": "testpass123"})
    return login_resp.json()["access_token"]


def test_completing_a_session_in_one_put_updates_athlete_stats():
    """Regression test: session.is_completed was being set by the generic
    field-update loop BEFORE the `if session_update.is_completed and not
    session.is_completed` guard ran, so the guard always saw it as already
    True and total_sessions/performance_rating never updated on a real
    single-PUT completion (exactly how the frontend calls it)."""
    token = _signup_and_login("completion_test_user")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        "/api/sessions/",
        json={"sport_type": "boxing", "session_type": "drill", "skill_name": "Jab"},
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    session_id = create_resp.json()["id"]

    me_before = client.get("/api/auth/me", headers=headers).json()
    assert me_before["total_sessions"] == 0

    put_resp = client.put(
        f"/api/sessions/{session_id}",
        json={
            "end_time": "2026-01-01T12:00:00",
            "duration_minutes": 10,
            "is_completed": True,
            "performance_score": 88.0,
            "technique_accuracy": 85.0,
            "balance_score": 90.0,
        },
        headers=headers,
    )
    assert put_resp.status_code == 200, put_resp.text

    me_after = client.get("/api/auth/me", headers=headers).json()
    assert me_after["total_sessions"] == 1
    assert me_after["performance_rating"] == 88.0


def test_completing_already_completed_session_does_not_double_count():
    token = _signup_and_login("completion_test_user_2")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        "/api/sessions/",
        json={"sport_type": "boxing", "session_type": "drill", "skill_name": "Jab"},
        headers=headers,
    )
    session_id = create_resp.json()["id"]

    body = {
        "end_time": "2026-01-01T12:00:00",
        "duration_minutes": 10,
        "is_completed": True,
        "performance_score": 80.0,
        "technique_accuracy": 80.0,
        "balance_score": 80.0,
    }
    client.put(f"/api/sessions/{session_id}", json=body, headers=headers)
    client.put(f"/api/sessions/{session_id}", json=body, headers=headers)

    me = client.get("/api/auth/me", headers=headers).json()
    assert me["total_sessions"] == 1


def test_completing_session_awards_gamification():
    token = _signup_and_login("gamification_route_test_user")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        "/api/sessions/",
        json={"sport_type": "boxing", "session_type": "drill", "skill_name": "Jab"},
        headers=headers,
    )
    session_id = create_resp.json()["id"]

    client.put(
        f"/api/sessions/{session_id}",
        json={
            "end_time": "2026-01-01T12:00:00",
            "duration_minutes": 10,
            "is_completed": True,
            "performance_score": 97.0,
            "technique_accuracy": 95.0,
            "balance_score": 90.0,
        },
        headers=headers,
    )

    gam = client.get("/api/gamification/me", headers=headers).json()
    assert gam["current_streak"] == 1
    codes = {a["code"] for a in gam["achievements"]}
    assert "first_session" in codes
    assert "high_score" in codes
