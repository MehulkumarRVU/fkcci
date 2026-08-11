import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from main import app

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


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_search_coaches_by_username():
    _signup_and_login("search_coach_1", role="coach")
    athlete_token = _signup_and_login("search_athlete_1")

    resp = client.get("/api/coaches/search?q=search_coach_1", headers=_headers(athlete_token))
    assert resp.status_code == 200, resp.text
    usernames = [c["username"] for c in resp.json()]
    assert "search_coach_1" in usernames


def test_request_accept_flow_sets_coach_id():
    coach_token = _signup_and_login("req_coach_1", role="coach")
    athlete_token = _signup_and_login("req_athlete_1")
    coach_id = client.get("/api/auth/me", headers=_headers(coach_token)).json()["id"]

    req_resp = client.post(f"/api/coaches/{coach_id}/request", headers=_headers(athlete_token))
    assert req_resp.status_code == 201, req_resp.text
    request_id = req_resp.json()["id"]

    pending = client.get("/api/coaches/me/requests", headers=_headers(coach_token))
    assert pending.status_code == 200
    assert any(r["id"] == request_id for r in pending.json())

    accept_resp = client.post(f"/api/coaches/requests/{request_id}/accept", headers=_headers(coach_token))
    assert accept_resp.status_code == 200, accept_resp.text
    assert accept_resp.json()["status"] == "accepted"

    me = client.get("/api/auth/me", headers=_headers(athlete_token)).json()
    assert me["coach_id"] == coach_id


def test_reject_request_does_not_set_coach_id():
    coach_token = _signup_and_login("req_coach_2", role="coach")
    athlete_token = _signup_and_login("req_athlete_2")
    coach_id = client.get("/api/auth/me", headers=_headers(coach_token)).json()["id"]

    req_resp = client.post(f"/api/coaches/{coach_id}/request", headers=_headers(athlete_token))
    request_id = req_resp.json()["id"]

    reject_resp = client.post(f"/api/coaches/requests/{request_id}/reject", headers=_headers(coach_token))
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    me = client.get("/api/auth/me", headers=_headers(athlete_token)).json()
    assert me["coach_id"] is None


def test_athlete_cannot_request_second_coach_while_connected():
    coach_token = _signup_and_login("req_coach_3", role="coach")
    other_coach_token = _signup_and_login("req_coach_4", role="coach")
    athlete_token = _signup_and_login("req_athlete_3")
    coach_id = client.get("/api/auth/me", headers=_headers(coach_token)).json()["id"]
    other_coach_id = client.get("/api/auth/me", headers=_headers(other_coach_token)).json()["id"]

    req_resp = client.post(f"/api/coaches/{coach_id}/request", headers=_headers(athlete_token))
    request_id = req_resp.json()["id"]
    client.post(f"/api/coaches/requests/{request_id}/accept", headers=_headers(coach_token))

    second_resp = client.post(f"/api/coaches/{other_coach_id}/request", headers=_headers(athlete_token))
    assert second_resp.status_code == 400


def test_unrelated_coach_cannot_accept_others_request():
    coach_token = _signup_and_login("req_coach_5", role="coach")
    unrelated_coach_token = _signup_and_login("req_coach_6", role="coach")
    athlete_token = _signup_and_login("req_athlete_5")
    coach_id = client.get("/api/auth/me", headers=_headers(coach_token)).json()["id"]

    req_resp = client.post(f"/api/coaches/{coach_id}/request", headers=_headers(athlete_token))
    request_id = req_resp.json()["id"]

    resp = client.post(f"/api/coaches/requests/{request_id}/accept", headers=_headers(unrelated_coach_token))
    assert resp.status_code == 404


def test_cancel_own_pending_request():
    coach_token = _signup_and_login("req_coach_7", role="coach")
    athlete_token = _signup_and_login("req_athlete_7")
    coach_id = client.get("/api/auth/me", headers=_headers(coach_token)).json()["id"]

    req_resp = client.post(f"/api/coaches/{coach_id}/request", headers=_headers(athlete_token))
    request_id = req_resp.json()["id"]

    cancel_resp = client.delete(f"/api/coaches/requests/{request_id}", headers=_headers(athlete_token))
    assert cancel_resp.status_code == 204

    pending = client.get("/api/coaches/me/requests", headers=_headers(coach_token))
    assert all(r["id"] != request_id for r in pending.json())


def test_invite_code_join_flow():
    coach_token = _signup_and_login("invite_coach_1", role="coach")
    athlete_token = _signup_and_login("invite_athlete_1")
    coach_id = client.get("/api/auth/me", headers=_headers(coach_token)).json()["id"]

    gen_resp = client.post("/api/coaches/me/invite-code", headers=_headers(coach_token))
    assert gen_resp.status_code == 200, gen_resp.text
    code = gen_resp.json()["code"]

    get_resp = client.get("/api/coaches/me/invite-code", headers=_headers(coach_token))
    assert get_resp.json()["code"] == code

    join_resp = client.post(f"/api/coaches/join/{code}", headers=_headers(athlete_token))
    assert join_resp.status_code == 200, join_resp.text
    assert join_resp.json()["id"] == coach_id

    me = client.get("/api/auth/me", headers=_headers(athlete_token)).json()
    assert me["coach_id"] == coach_id


def test_regenerating_invite_code_revokes_old_code():
    coach_token = _signup_and_login("invite_coach_2", role="coach")
    athlete_token = _signup_and_login("invite_athlete_2")

    first_resp = client.post("/api/coaches/me/invite-code", headers=_headers(coach_token))
    old_code = first_resp.json()["code"]

    client.post("/api/coaches/me/invite-code", headers=_headers(coach_token))

    join_resp = client.post(f"/api/coaches/join/{old_code}", headers=_headers(athlete_token))
    assert join_resp.status_code == 404


def test_invalid_invite_code_rejected():
    athlete_token = _signup_and_login("invite_athlete_3")
    resp = client.post("/api/coaches/join/not-a-real-code", headers=_headers(athlete_token))
    assert resp.status_code == 404


def test_disconnect_by_coach_and_by_athlete():
    coach_token = _signup_and_login("disc_coach_1", role="coach")
    athlete_token = _signup_and_login("disc_athlete_1")
    coach_id = client.get("/api/auth/me", headers=_headers(coach_token)).json()["id"]
    athlete_id = client.get("/api/auth/me", headers=_headers(athlete_token)).json()["id"]

    req_resp = client.post(f"/api/coaches/{coach_id}/request", headers=_headers(athlete_token))
    client.post(f"/api/coaches/requests/{req_resp.json()['id']}/accept", headers=_headers(coach_token))

    disconnect_resp = client.delete(f"/api/coaches/me/athletes/{athlete_id}", headers=_headers(coach_token))
    assert disconnect_resp.status_code == 204

    me = client.get("/api/auth/me", headers=_headers(athlete_token)).json()
    assert me["coach_id"] is None

    # Reconnect, then have the athlete leave on their own
    req_resp2 = client.post(f"/api/coaches/{coach_id}/request", headers=_headers(athlete_token))
    client.post(f"/api/coaches/requests/{req_resp2.json()['id']}/accept", headers=_headers(coach_token))

    leave_resp = client.post("/api/coaches/me/leave", headers=_headers(athlete_token))
    assert leave_resp.status_code == 204

    me2 = client.get("/api/auth/me", headers=_headers(athlete_token)).json()
    assert me2["coach_id"] is None


def test_connection_status_reflects_pending_then_connected():
    coach_token = _signup_and_login("status_coach_1", role="coach")
    athlete_token = _signup_and_login("status_athlete_1")
    coach_id = client.get("/api/auth/me", headers=_headers(coach_token)).json()["id"]

    status_before = client.get("/api/coaches/me/connection-status", headers=_headers(athlete_token)).json()
    assert status_before["connected_coach"] is None
    assert status_before["pending_request"] is None

    req_resp = client.post(f"/api/coaches/{coach_id}/request", headers=_headers(athlete_token))
    status_pending = client.get("/api/coaches/me/connection-status", headers=_headers(athlete_token)).json()
    assert status_pending["pending_request"]["id"] == req_resp.json()["id"]

    client.post(f"/api/coaches/requests/{req_resp.json()['id']}/accept", headers=_headers(coach_token))
    status_connected = client.get("/api/coaches/me/connection-status", headers=_headers(athlete_token)).json()
    assert status_connected["connected_coach"]["id"] == coach_id


def test_athlete_cannot_call_coach_only_endpoints():
    athlete_token = _signup_and_login("perm_athlete_1")
    resp = client.get("/api/coaches/me/requests", headers=_headers(athlete_token))
    assert resp.status_code == 403


def test_coach_cannot_call_athlete_only_endpoints():
    coach_token = _signup_and_login("perm_coach_1", role="coach")
    resp = client.get("/api/coaches/search?q=x", headers=_headers(coach_token))
    assert resp.status_code == 403
