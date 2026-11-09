from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from app.routes import auth as auth_routes
from backend.app.routes.auth import get_password_hash
from backend.app.models.athlete import Athlete
from backend.app.models.refresh_token import RefreshToken
from backend.app.config import settings


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


def test_login_rejects_password_changed_during_verification(
    client: TestClient,
    create_athlete,
    db_session,
    monkeypatch,
):
    stored_hash = create_athlete.hashed_password
    replacement_hash = get_password_hash("new-password123")

    async def change_password_after_verification(_auth_service, _password, checked_hash):
        assert checked_hash == stored_hash
        db_session.query(Athlete).filter(Athlete.id == create_athlete.id).update(
            {Athlete.hashed_password: replacement_hash}
        )
        db_session.commit()
        return True

    monkeypatch.setattr(
        auth_routes,
        "verify_password_for_request",
        change_password_after_verification,
    )
    response = client.post(
        "/api/auth/login",
        data={"username": create_athlete.username, "password": "password123"},
    )

    assert response.status_code == 401, response.text
    assert db_session.query(RefreshToken).count() == 0


def test_legacy_refresh_alias_requires_and_rotates_refresh_token(
    client: TestClient,
    create_athlete,
):
    login_response = client.post(
        "/api/auth/login",
        data={"username": create_athlete.username, "password": "password123"},
    )
    assert login_response.status_code == 200
    old_refresh = login_response.json()["refresh_token"]

    access_only = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )
    assert access_only.status_code == 422

    refreshed = client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != old_refresh

    replayed = client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert replayed.status_code == 401


def test_readiness_endpoint_and_request_correlation_id(client: TestClient):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"
    assert response.headers["X-Request-ID"]


def test_legacy_access_token_remains_valid_until_its_expiration(client: TestClient, create_athlete):
    legacy_token = jwt.encode(
        {
            "sub": create_athlete.username,
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    existing_session = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {legacy_token}"},
    )
    assert existing_session.status_code == 200
    assert existing_session.json()["username"] == create_athlete.username

    expired_token = jwt.encode(
        {
            "sub": create_athlete.username,
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    expired_session = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert expired_session.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient, create_athlete):
    login_response = client.post(
        "/api/auth/login",
        data={"username": create_athlete.username, "password": "password123"},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Logged out"}

    refresh_response = client.post(
        "/api/auth/token/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401

    repeated_logout = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert repeated_logout.status_code == 200


def test_refresh_rotates_token_and_uses_15_minute_access_lifetime(client: TestClient, create_athlete):
    login_response = client.post(
        "/api/auth/login",
        data={"username": create_athlete.username, "password": "password123"},
    )
    assert login_response.status_code == 200
    old_refresh = login_response.json()["refresh_token"]
    access_claims = jwt.decode(
        login_response.json()["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    assert access_claims["exp"] - access_claims["iat"] == 15 * 60

    refreshed = client.post(
        "/api/auth/token/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refreshed.status_code == 200, refreshed.text
    new_refresh = refreshed.json()["refresh_token"]
    assert new_refresh != old_refresh

    old_token_reuse = client.post(
        "/api/auth/token/refresh",
        json={"refresh_token": old_refresh},
    )
    assert old_token_reuse.status_code == 401

    next_refresh = client.post(
        "/api/auth/token/refresh",
        json={"refresh_token": new_refresh},
    )
    assert next_refresh.status_code == 200, next_refresh.text
    renewed_claims = jwt.decode(
        next_refresh.json()["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    assert renewed_claims["exp"] - renewed_claims["iat"] == 15 * 60


def test_inactive_athlete_cannot_use_access_or_refresh_tokens(client: TestClient, create_athlete, db_session):
    login_response = client.post(
        "/api/auth/login",
        data={"username": create_athlete.username, "password": "password123"},
    )
    assert login_response.status_code == 200
    create_athlete.is_active = False
    db_session.commit()

    protected = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )
    assert protected.status_code == 403

    refreshed = client.post(
        "/api/auth/token/refresh",
        json={"refresh_token": login_response.json()["refresh_token"]},
    )
    assert refreshed.status_code == 403


def test_refresh_token_input_validation(client: TestClient):
    response = client.post("/api/auth/token/refresh", json={"refresh_token": "short"})
    assert response.status_code == 422


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


def test_adaptive_capabilities_only_report_categories_with_exercises(client: TestClient):
    response = client.get("/api/adaptive/capabilities")
    assert response.status_code == 200
    capabilities = {item["category"]: item for item in response.json()}
    assert capabilities["boxing"]["adaptive_supported"] is True
    assert capabilities["calisthenics"]["adaptive_supported"] is False
    assert "No adaptive exercise" in capabilities["calisthenics"]["note"]


def test_session_rejects_adaptive_exercise_from_another_category(client: TestClient):
    signup = client.post(
        "/api/auth/signup",
        json={
            "email": "adaptive-category@example.com",
            "username": "adaptive_category_user",
            "password": "secret123",
            "sport_type": "calisthenics",
        },
    )
    assert signup.status_code == 201, signup.text
    login = client.post(
        "/api/auth/login",
        data={"username": "adaptive_category_user", "password": "secret123"},
    )
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    response = client.post(
        "/api/sessions/",
        headers=headers,
        json={
            "sport_type": "calisthenics",
            "session_type": "drill",
            "adaptive": {
                "setup": "standing",
                "exercise": "adaptive_punch",
                "camera_view": "front",
            },
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Adaptive exercise is unavailable for this category"
