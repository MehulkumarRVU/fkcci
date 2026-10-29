import pytest
from fastapi.testclient import TestClient
from backend.app.routes.auth import get_password_hash
from backend.app.models.athlete import Athlete


@pytest.fixture(scope="function")
def create_athlete(db_session):
    athlete = Athlete(
        email="testuser@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        role="athlete",
        sport_type="boxing",
        linked_sports="boxing",
        skill_level="beginner",
    )
    db_session.add(athlete)
    db_session.commit()
    db_session.refresh(athlete)
    return athlete


def test_signup_and_login_flow(client: TestClient):
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "password123",
            "sport_type": "boxing",
            "skill_level": "beginner",
        },
    )
    assert response.status_code == 201, response.text
    athlete = response.json()
    assert athlete["username"] == "testuser"
    assert athlete["role"] == "athlete"

    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "password123"},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer " + token},
    )
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["username"] == "testuser"
    assert me_response.json()["sport_type"] == "boxing"


def test_coach_signup_and_role_field(client: TestClient):
    coach_response = client.post(
        "/api/auth/signup-coach",
        json={
            "email": "testcoach@example.com",
            "username": "testcoach",
            "password": "secret123",
        },
    )
    assert coach_response.status_code == 201
    assert coach_response.json()["role"] == "coach"

    athlete_response = client.post(
        "/api/auth/signup",
        json={
            "email": "testathlete@example.com",
            "username": "testathlete",
            "password": "secret123",
            "sport_type": "boxing",
        },
    )
    assert athlete_response.status_code == 201
    assert athlete_response.json()["role"] == "athlete"

    coach_login = client.post(
        "/api/auth/login",
        data={"username": "testcoach", "password": "secret123"},
    )
    assert coach_login.status_code == 200
    token = coach_login.json()["access_token"]
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer " + token},
    )
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "coach"


def test_adaptive_profile_persists_and_can_be_removed(client: TestClient):
    signup = client.post(
        "/api/auth/signup",
        json={
            "email": "adaptive@example.com",
            "username": "adaptive_user",
            "password": "secret123",
            "sport_type": "gym",
            "adaptive_profile": {
                "enabled": True,
                "preferred_setup": "seated",
                "accessibility_preferences": ["captions"],
            },
        },
    )
    assert signup.status_code == 201, signup.text
    assert signup.json()["adaptive_mode_enabled"] is True

    login = client.post(
        "/api/auth/login",
        data={"username": "adaptive_user", "password": "secret123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": "Bearer " + token}

    profile = client.get("/api/adaptive/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["profile"]["preferred_setup"] == "seated"

    updated = client.put(
        "/api/adaptive/profile",
        headers=headers,
        json={"enabled": False, "preferred_setup": "seated"},
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert updated.json()["profile"]["preferred_setup"] == "seated"

    removed = client.delete("/api/adaptive/profile", headers=headers)
    assert removed.status_code == 204
