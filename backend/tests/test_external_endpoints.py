import pytest
from fastapi.testclient import TestClient
from backend.app.database import SessionLocal
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
    # create athlete
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "password123",
            "sport_type": "boxing",
            "skill_level": "beginner"
        }
    )
    assert response.status_code == 201, response.text
    athlete = response.json()
    assert athlete["username"] == "testuser"
    assert athlete["role"] == "athlete"

    # login
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "password123"}
    )
    assert login_response.status_code == 200, login_response.text
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    access_token = token_data["access_token"]
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 200, me_response.text
    user_info = me_response.json()
    assert user_info["username"] == "testuser"
    assert user_info["sport_type"] == "boxing"


def test_coach_signup_and_role_field(client: TestClient):
    coach_response = client.post(
        "/api/auth/signup-coach",
        json={
            "email": "testcoach@example.com",
            "username": "testcoach",
            "password": "secret123"
        }
    )
    assert coach_response.status_code == 201
    coach_data = coach_response.json()
    assert coach_data["role"] == "coach"

    athlete_response = client.post(
        "/api/auth/signup",
        json={
            "email": "testathlete@example.com",
            "username": "testathlete",
            "password": "secret123",
            "sport_type": "boxing"
        }
    )
    assert athlete_response.status_code == 201
    athlete_data = athlete_response.json()
    assert athlete_data["role"] == "athlete"

    coach_login = client.post(
        "/api/auth/login",
        data={"username": "testcoach", "password": "secret123"}
    )
    assert coach_login.status_code == 200
    token = coach_login.json()["access_token"]

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "coach"
