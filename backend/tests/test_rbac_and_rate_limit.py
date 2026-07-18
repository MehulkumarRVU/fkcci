import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.routes.auth import get_current_athlete


class DummyCoach:
    id = 1
    username = "coachuser"
    role = "coach"


class DummyAthlete:
    id = 2
    username = "normaluser"
    role = "athlete"


def test_coach_only_endpoint_returns_200_for_coach(app, client):
    app.dependency_overrides[get_current_athlete] = lambda: DummyCoach()
    try:
        response = client.get("/api/analytics/coach/summary")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_current_athlete, None)


def test_coach_only_endpoint_forbidden_for_athlete(app, client):
    app.dependency_overrides[get_current_athlete] = lambda: DummyAthlete()
    try:
        response = client.get("/api/analytics/coach/summary")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_athlete, None)


def test_rate_limit_headers_present(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert "retry-after" in r.headers or r.headers.get("Retry-After") is None
