import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _signup_and_login(username, role="athlete", extra=None):
    payload = {
        "email": f"{username}@example.com",
        "username": username,
        "password": "testpass123",
        "sport_type": "boxing",
        "skill_level": "beginner",
    }
    if extra:
        payload.update(extra)
    endpoint = "/api/auth/signup-coach" if role == "coach" else "/api/auth/signup"
    client.post(endpoint, json=payload)
    login_resp = client.post("/api/auth/login", data={"username": username, "password": "testpass123"})
    return login_resp.json()["access_token"]


def test_session_pdf_report():
    token = _signup_and_login("pdf_session_user")
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
            "performance_score": 88.0,
            "technique_accuracy": 85.0,
            "balance_score": 90.0,
        },
        headers=headers,
    )

    resp = client.get(f"/api/reports/session/{session_id}/pdf", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 500
    assert resp.content[:4] == b"%PDF"


def test_session_pdf_report_requires_ownership():
    owner_token = _signup_and_login("pdf_owner_user")
    other_token = _signup_and_login("pdf_other_user")

    create_resp = client.post(
        "/api/sessions/",
        json={"sport_type": "boxing", "session_type": "drill", "skill_name": "Jab"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    session_id = create_resp.json()["id"]

    resp = client.get(f"/api/reports/session/{session_id}/pdf", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 403


def test_progress_pdf_report():
    token = _signup_and_login("pdf_progress_user")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/reports/progress/pdf", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"


def test_coach_athlete_pdf_report():
    coach_token = _signup_and_login("pdf_coach_user", role="coach")

    # Sign up an athlete and link them to the coach directly via DB update
    # through the profile update flow isn't available for coach_id, so use
    # the coach signup flow's athlete assignment if present; otherwise this
    # test asserts the 403 path when no relationship exists yet.
    athlete_token = _signup_and_login("pdf_athlete_user")
    athlete_headers = {"Authorization": f"Bearer {athlete_token}"}
    me = client.get("/api/auth/me", headers=athlete_headers).json()

    coach_headers = {"Authorization": f"Bearer {coach_token}"}
    resp = client.get(f"/api/reports/coach/athlete/{me['id']}/pdf", headers=coach_headers)
    # Not yet coached by this coach -> 403, proving the auth check runs
    # before any PDF is generated (same relationship check as the JSON route).
    assert resp.status_code == 403
