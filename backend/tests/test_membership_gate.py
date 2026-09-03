import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal
from app.models.athlete import Athlete

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


def _create_session(token):
    return client.post(
        "/api/sessions/",
        json={"sport_type": "boxing", "session_type": "drill", "skill_name": "Jab"},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_free_tier_blocked_after_five_sessions_in_30_days():
    token = _signup_and_login("gate_free_athlete")

    for i in range(5):
        resp = _create_session(token)
        assert resp.status_code == 201, f"session {i} failed: {resp.text}"

    sixth = _create_session(token)
    # 402 Payment Required, not 403 - a 403 here would make the frontend's
    # fetchWithAuth() treat this plan-limit rejection as an expired/invalid
    # session and force-log the athlete out.
    assert sixth.status_code == 402
    assert "Free tier is limited" in sixth.json()["detail"]


def test_pro_tier_unlimited():
    token = _signup_and_login("gate_pro_athlete")

    with SessionLocal() as db:
        athlete = db.query(Athlete).filter(Athlete.username == "gate_pro_athlete").first()
        athlete.membership_tier = "pro"
        db.commit()

    for i in range(7):
        resp = _create_session(token)
        assert resp.status_code == 201, f"pro session {i} failed: {resp.text}"
