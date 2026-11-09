import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.routes.auth import get_current_athlete
from app.models.athlete import Athlete
from app.models.session import Session
from app.routes.auth import get_password_hash


def test_coach_analytics_endpoints(app, client, db_session):
    coach = Athlete(
        email="coach-analytics@example.com",
        username="coach_analytics",
        hashed_password=get_password_hash("secret123"),
        role="coach",
        sport_type="boxing",
        linked_sports="boxing,table_tennis"
    )
    db_session.add(coach)
    db_session.commit()
    db_session.refresh(coach)

    athlete_one = Athlete(
        email="athlete1@example.com",
        username="athlete_one",
        hashed_password=get_password_hash("password123"),
        role="athlete",
        coach_id=coach.id,
        sport_type="boxing",
        linked_sports="boxing",
        skill_level="beginner"
    )
    athlete_two = Athlete(
        email="athlete2@example.com",
        username="athlete_two",
        hashed_password=get_password_hash("password123"),
        role="athlete",
        coach_id=coach.id,
        sport_type="table_tennis",
        linked_sports="table_tennis",
        skill_level="intermediate"
    )

    db_session.add_all([athlete_one, athlete_two])
    db_session.commit()
    db_session.refresh(athlete_one)
    db_session.refresh(athlete_two)

    now = datetime.now(timezone.utc)
    sessions = [
        Session(
            athlete_id=athlete_one.id,
            sport_type="boxing",
            session_type="drill",
            start_time=now - timedelta(days=1),
            end_time=now - timedelta(days=1, minutes=-30),
            duration_minutes=30,
            is_completed=True,
            performance_score=75.0,
            technique_accuracy=78.0,
            reaction_score=72.0,
            balance_score=70.0,
            created_at=now - timedelta(days=1)
        ),
        Session(
            athlete_id=athlete_two.id,
            sport_type="table_tennis",
            session_type="drill",
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=2, minutes=-25),
            duration_minutes=25,
            is_completed=True,
            performance_score=82.0,
            technique_accuracy=85.0,
            reaction_score=80.0,
            balance_score=78.0,
            created_at=now - timedelta(days=2)
        ),
        Session(
            athlete_id=athlete_two.id,
            sport_type="table_tennis",
            session_type="match_simulation",
            start_time=now - timedelta(days=3),
            end_time=now - timedelta(days=3, minutes=-40),
            duration_minutes=40,
            is_completed=True,
            performance_score=88.0,
            technique_accuracy=90.0,
            reaction_score=87.0,
            balance_score=88.0,
            created_at=now - timedelta(days=3)
        )
    ]
    db_session.add_all(sessions)
    db_session.commit()

    app.dependency_overrides[get_current_athlete] = lambda: coach
    try:
        athletes_response = client.get("/api/analytics/coach/athletes")
        assert athletes_response.status_code == 200, athletes_response.text
        athlete_list = athletes_response.json()
        assert len(athlete_list) == 2
        assert {a["username"] for a in athlete_list} == {"athlete_one", "athlete_two"}

        summary_response = client.get("/api/analytics/coach/summary")
        assert summary_response.status_code == 200, summary_response.text
        summary = summary_response.json()
        assert summary["total_athletes"] == 2
        assert summary["total_sessions_this_month"] == 3
        assert summary["completed_sessions_this_month"] == 3
        assert summary["most_active_athlete"]["username"] == "athlete_two"
        assert len(summary["top_performers"]) == 2

        monthly_report_response = client.get(f"/api/analytics/coach/athlete/{athlete_two.id}/monthly-report")
        assert monthly_report_response.status_code == 200, monthly_report_response.text
        report = monthly_report_response.json()
        assert report["athlete_id"] == athlete_two.id
        assert report["athlete_username"] == athlete_two.username
        assert report["total_sessions"] == 2
        assert report["monthly_stats"]["completed_sessions"] == 2
        assert len(report["recent_sessions"]) == 2
    finally:
        app.dependency_overrides.pop(get_current_athlete, None)
