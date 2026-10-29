import sys
import os

# Ensure `backend` is on sys.path so `app.*` imports resolve during pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.pose_engine.analyzer_factory import AnalyzerFactory
from main import app


client = TestClient(app)


def setup_module(module):
    # Bypass auth dependency for analysis endpoint tests
    class DummyUser:
        username = "testuser"
        id = 1

    from app.routes.auth import get_current_athlete
    app.dependency_overrides[get_current_athlete] = lambda: DummyUser()


def teardown_module(module):
    from app.routes.auth import get_current_athlete
    app.dependency_overrides.pop(get_current_athlete, None)


def sample_landmark(x=0.5, y=0.5, v=0.9):
    return {"x": x, "y": y, "z": 0.0, "visibility": v}


def make_frame():
    # Create 33 landmarks with default positions (some variation)
    landmarks = [sample_landmark() for _ in range(33)]
    # adjust shoulders and wrists
    landmarks[11]["x"] = 0.45
    landmarks[12]["x"] = 0.55
    landmarks[15]["x"] = 0.6
    landmarks[16]["x"] = 0.4
    landmarks[0]["x"] = 0.5  # nose
    return landmarks


def test_supported_racket_analyze_endpoint():
    payload = {
        "sport_type": "badminton",
        "skill_name": "Serve Technique",
        "pose_data": [
            {"landmarks": make_frame(), "timestamp": 0.0},
            {"landmarks": make_frame(), "timestamp": 0.033},
        ],
    }

    resp = client.post("/api/analysis/analyze", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["sport_type"] == "badminton"
    assert "overall_score" in data
    assert isinstance(data["feedback_messages"], list)
