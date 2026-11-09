from sqlalchemy import create_engine, inspect, text

from backend.app.database import ensure_compatibility_columns


def test_compatibility_columns_upgrade_legacy_sqlite_schema():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE athletes (id INTEGER PRIMARY KEY, sport_type VARCHAR NOT NULL)"
        ))
        connection.execute(text(
            "CREATE TABLE sessions (id INTEGER PRIMARY KEY, start_time DATETIME, end_time DATETIME)"
        ))
        connection.execute(text(
            "INSERT INTO athletes (id, sport_type) VALUES (1, 'boxing')"
        ))
        connection.execute(text(
            "INSERT INTO sessions (id, start_time) VALUES (1, '2026-01-02 03:04:05')"
        ))

        ensure_compatibility_columns(connection)
        ensure_compatibility_columns(connection)

        athlete_columns = {column["name"] for column in inspect(connection).get_columns("athletes")}
        session_columns = {column["name"] for column in inspect(connection).get_columns("sessions")}
        athlete = connection.execute(
            text("SELECT linked_sports, role, adaptive_mode_enabled FROM athletes WHERE id = 1")
        ).one()
        created_at = connection.execute(
            text("SELECT created_at FROM sessions WHERE id = 1")
        ).scalar_one()

    assert {
        "linked_sports", "role", "coach_id", "current_streak", "longest_streak",
        "last_session_date", "adaptive_mode_enabled", "adaptive_profile",
    }.issubset(athlete_columns)
    assert {
        "scoring_version", "skill_name", "joint_summary", "adaptive_mode",
        "adaptive_setup", "adaptive_exercise", "adaptive_reference", "created_at",
    }.issubset(session_columns)
    assert athlete == ("", "athlete", False)
    assert str(created_at).startswith("2026-01-02 03:04:05")
    engine.dispose()
