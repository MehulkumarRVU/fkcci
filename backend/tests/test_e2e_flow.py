import sys
import os

# Ensure `backend` is on sys.path so `app.*` imports resolve during pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def sample_landmark(x=0.5, y=0.5, v=0.9):
    return {"x": x, "y": y, "z": 0.0, "visibility": v}


def make_frame():
    landmarks = [sample_landmark() for _ in range(33)]
    landmarks[11]["x"] = 0.45
    landmarks[12]["x"] = 0.55
    landmarks[15]["x"] = 0.6
    landmarks[16]["x"] = 0.4
    landmarks[0]["x"] = 0.5
    return landmarks


def test_e2e_signup_login_and_analysis():
    # signup
    username = "e2e_user"
    email = "e2e_user@example.com"
    password = "testpass123"

    resp = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "username": username,
            "password": password,
            "sport_type": "badminton",
            "skill_level": "beginner",
        },
    )
    assert resp.status_code == 201, resp.text

    # login (OAuth2 form-encoded)
    login_resp = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert login_resp.status_code == 200, login_resp.text
    token_data = login_resp.json()
    assert "access_token" in token_data

    access_token = token_data["access_token"]

    # get profile
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 200, me_resp.text
    assert me_resp.json()["username"] == username

    # analysis request
    payload = {
        "sport_type": "badminton",
        "skill_name": "Serve Technique",
        "pose_data": [
            {"landmarks": make_frame(), "timestamp": 0.0},
            {"landmarks": make_frame(), "timestamp": 0.033},
        ],
    }
    analysis_resp = client.post("/api/analysis/analyze", json=payload, headers={"Authorization": f"Bearer {access_token}"})
    assert analysis_resp.status_code == 200, analysis_resp.text
    data = analysis_resp.json()
    assert data["sport_type"] == "badminton"
    assert "overall_score" in data
