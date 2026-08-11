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


def _signup_and_login(username, role="athlete"):
    endpoint = "/api/auth/signup-coach" if role == "coach" else "/api/auth/signup"
    client.post(
        endpoint,
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


def _link_coach(athlete_username, coach_username):
    with SessionLocal() as db:
        coach = db.query(Athlete).filter(Athlete.username == coach_username).first()
        athlete = db.query(Athlete).filter(Athlete.username == athlete_username).first()
        athlete.coach_id = coach.id
        db.commit()
        return athlete.id


def test_athlete_can_post_and_read_own_thread():
    token = _signup_and_login("notes_athlete_1")
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/auth/me", headers=headers).json()

    post_resp = client.post(f"/api/notes/athlete/{me['id']}", json={"message": "Note to self"}, headers=headers)
    assert post_resp.status_code == 201, post_resp.text

    get_resp = client.get(f"/api/notes/athlete/{me['id']}", headers=headers)
    assert get_resp.status_code == 200
    notes = get_resp.json()
    assert len(notes) == 1
    assert notes[0]["message"] == "Note to self"
    assert notes[0]["is_coach"] is False


def test_coach_can_post_to_their_athletes_thread():
    coach_token = _signup_and_login("notes_coach_1", role="coach")
    athlete_token = _signup_and_login("notes_athlete_2")
    athlete_headers = {"Authorization": f"Bearer {athlete_token}"}
    athlete_id = client.get("/api/auth/me", headers=athlete_headers).json()["id"]

    _link_coach("notes_athlete_2", "notes_coach_1")

    coach_headers = {"Authorization": f"Bearer {coach_token}"}
    post_resp = client.post(
        f"/api/notes/athlete/{athlete_id}",
        json={"message": "Great form today!"},
        headers=coach_headers,
    )
    assert post_resp.status_code == 201, post_resp.text
    assert post_resp.json()["is_coach"] is True

    # Athlete can read the coach's note in their own thread
    get_resp = client.get(f"/api/notes/athlete/{athlete_id}", headers=athlete_headers)
    messages = [n["message"] for n in get_resp.json()]
    assert "Great form today!" in messages


def test_unrelated_coach_cannot_access_thread():
    unrelated_coach_token = _signup_and_login("notes_coach_2", role="coach")
    athlete_token = _signup_and_login("notes_athlete_3")
    athlete_id = client.get("/api/auth/me", headers={"Authorization": f"Bearer {athlete_token}"}).json()["id"]

    resp = client.get(
        f"/api/notes/athlete/{athlete_id}",
        headers={"Authorization": f"Bearer {unrelated_coach_token}"},
    )
    assert resp.status_code == 403


def test_unrelated_athlete_cannot_access_others_thread():
    athlete_a_token = _signup_and_login("notes_athlete_4")
    athlete_b_token = _signup_and_login("notes_athlete_5")
    athlete_a_id = client.get("/api/auth/me", headers={"Authorization": f"Bearer {athlete_a_token}"}).json()["id"]

    resp = client.post(
        f"/api/notes/athlete/{athlete_a_id}",
        json={"message": "snooping"},
        headers={"Authorization": f"Bearer {athlete_b_token}"},
    )
    assert resp.status_code == 403


def test_empty_message_rejected():
    token = _signup_and_login("notes_athlete_6")
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/auth/me", headers=headers).json()

    resp = client.post(f"/api/notes/athlete/{me['id']}", json={"message": "   "}, headers=headers)
    assert resp.status_code == 400
