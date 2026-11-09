import sys
import os

# Ensure `backend` is on sys.path so `app.*` imports resolve during pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.pose_engine.analyzer_factory import AnalyzerFactory
from main import app


def make_simple_landmarks():
    # create 33 landmarks with simple coordinates
    lm = []
    for i in range(33):
        lm.append({"x": float(i) * 0.01, "y": float(i) * 0.01, "z": 0.0, "visibility": 1.0})
    return lm


def test_analyzer_factory_and_analyzers():
    for sport in ("boxing", "table_tennis", "badminton"):
        analyzer = AnalyzerFactory.get_analyzer(sport)
        assert analyzer is not None
        landmarks = make_simple_landmarks()
        res = analyzer.analyze_frame(landmarks, "Jab" if sport == "boxing" else "Forehand Drive")
        assert isinstance(res, dict)
        assert "score" in res
        assert "technique_accuracy" in res
        assert "balance_score" in res
        assert "feedback" in res


def test_analysis_api_endpoint_override_auth():
    # override auth dependency to bypass JWT
    class DummyUser:
        username = "testuser"
        id = 1

    from app.routes.auth import get_current_athlete

    app.dependency_overrides[get_current_athlete] = lambda: DummyUser()

    client = TestClient(app)
    landmarks = make_simple_landmarks()
    payload = {
        "sport_type": "boxing",
        "skill_name": "Jab",
        "pose_data": [{"landmarks": landmarks, "timestamp": 0.0}]
    }

    try:
        resp = client.post("/api/analysis/analyze", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["sport_type"] == "boxing"
        assert "overall_score" in data
    finally:
        app.dependency_overrides.pop(get_current_athlete, None)


def test_analysis_api_rejects_unreliable_pose_without_score():
    class DummyUser:
        username = "testuser"
        id = 1

    from app.routes.auth import get_current_athlete

    app.dependency_overrides[get_current_athlete] = lambda: DummyUser()
    client = TestClient(app)
    landmarks = make_simple_landmarks()
    for landmark in landmarks:
        landmark["visibility"] = 0.0
    try:
        response = client.post("/api/analysis/realtime-feedback", json={
            "sport_type": "boxing",
            "skill_name": "Jab",
            "landmarks": landmarks,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["score"] is None
        assert data["evaluation_status"] == "insufficient_evidence"
        assert data["reliability_reasons"]
    finally:
        app.dependency_overrides.pop(get_current_athlete, None)


def test_analysis_api_rejects_unknown_skill():
    class DummyUser:
        username = "testuser"
        id = 1

    from app.routes.auth import get_current_athlete

    app.dependency_overrides[get_current_athlete] = lambda: DummyUser()
    client = TestClient(app)
    try:
        response = client.post("/api/analysis/realtime-feedback", json={
            "sport_type": "boxing",
            "skill_name": "Invented Movement",
            "landmarks": make_simple_landmarks(),
        })
        assert response.status_code == 400
        assert response.json()["detail"]["supported_skills"]
    finally:
        app.dependency_overrides.pop(get_current_athlete, None)


def test_adaptive_realtime_feedback_rejects_exercise_for_wrong_category():
    class DummyUser:
        username = "testuser"
        id = 1

    from app.routes.auth import get_current_athlete

    app.dependency_overrides[get_current_athlete] = lambda: DummyUser()
    client = TestClient(app)
    try:
        response = client.post("/api/analysis/realtime-feedback", json={
            "sport_type": "calisthenics",
            "skill_name": "Basic Calisthenics Technique",
            "landmarks": make_simple_landmarks(),
            "adaptive": {
                "setup": "standing",
                "exercise": "adaptive_punch",
                "camera_view": "front",
            },
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Adaptive exercise is unavailable for this category"
    finally:
        app.dependency_overrides.pop(get_current_athlete, None)


def test_adaptive_session_analysis_rejects_exercise_for_wrong_category():
    class DummyUser:
        username = "testuser"
        id = 1

    from app.routes.auth import get_current_athlete

    app.dependency_overrides[get_current_athlete] = lambda: DummyUser()
    client = TestClient(app)
    try:
        response = client.post("/api/analysis/analyze", json={
            "sport_type": "calisthenics",
            "skill_name": "Basic Calisthenics Technique",
            "pose_data": [{"landmarks": make_simple_landmarks(), "timestamp": 0.0}],
            "adaptive": {
                "setup": "standing",
                "exercise": "adaptive_punch",
                "camera_view": "front",
            },
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Adaptive exercise is unavailable for this category"
    finally:
        app.dependency_overrides.pop(get_current_athlete, None)
