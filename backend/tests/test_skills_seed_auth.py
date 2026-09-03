import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_seed_skills_requires_authentication():
    """POST /api/skills/seed previously had no auth check at all - any
    unauthenticated caller could trigger it in production."""
    resp = client.post("/api/skills/seed")
    assert resp.status_code == 401


def test_seed_skills_works_for_logged_in_athlete():
    client.post(
        "/api/auth/signup",
        json={
            "email": "seedtest@example.com",
            "username": "seedtest_athlete",
            "password": "testpass123",
            "sport_type": "boxing",
            "skill_level": "beginner",
        },
    )
    login_resp = client.post("/api/auth/login", data={"username": "seedtest_athlete", "password": "testpass123"})
    token = login_resp.json()["access_token"]

    resp = client.post("/api/skills/seed", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
