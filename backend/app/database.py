from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///./"):
    project_root = Path(__file__).resolve().parents[1]
    sqlite_path = project_root / SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{sqlite_path.as_posix()}"

CONNECT_ARGS = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=CONNECT_ARGS)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
DATABASE_INITIALIZATION_LOCK_ID = 0x504F434B45544348


def ensure_compatibility_columns(connection) -> None:
    compatibility_columns = {
        "athletes": {
            "linked_sports": "VARCHAR DEFAULT '' NOT NULL",
            "role": "VARCHAR DEFAULT 'athlete' NOT NULL",
            "coach_id": "INTEGER",
            "current_streak": "INTEGER DEFAULT 0",
            "longest_streak": "INTEGER DEFAULT 0",
            "last_session_date": "DATE",
            "adaptive_mode_enabled": "BOOLEAN DEFAULT FALSE NOT NULL",
            "adaptive_profile": "JSON",
        },
        "sessions": {
            "scoring_version": "VARCHAR DEFAULT 'v1'",
            "skill_name": "VARCHAR",
            "joint_summary": "JSON",
            "adaptive_mode": "BOOLEAN DEFAULT FALSE NOT NULL",
            "adaptive_setup": "VARCHAR",
            "adaptive_exercise": "VARCHAR",
            "adaptive_reference": "JSON",
            "created_at": (
                "TIMESTAMP WITH TIME ZONE"
                if connection.dialect.name == "postgresql"
                else "DATETIME"
            ),
        },
    }

    schema = inspect(connection)
    for table_name, columns in compatibility_columns.items():
        existing_columns = {column["name"] for column in schema.get_columns(table_name)}
        for column_name, definition in columns.items():
            if column_name not in existing_columns:
                connection.execute(text(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
                ))

    connection.execute(text(
        """
        UPDATE sessions
        SET created_at = COALESCE(created_at, end_time, start_time, CURRENT_TIMESTAMP)
        WHERE created_at IS NULL
        """
    ))

    if connection.dialect.name != "postgresql":
        return

    athlete_foreign_keys = inspect(connection).get_foreign_keys("athletes")
    if not any(key.get("constrained_columns") == ["coach_id"] for key in athlete_foreign_keys):
        connection.execute(text(
            "ALTER TABLE athletes ADD CONSTRAINT fk_athletes_coach_id "
            "FOREIGN KEY (coach_id) REFERENCES athletes (id) NOT VALID"
        ))
        connection.execute(text(
            "ALTER TABLE athletes VALIDATE CONSTRAINT fk_athletes_coach_id"
        ))

    session_foreign_keys = inspect(connection).get_foreign_keys("sessions")
    if not any(key.get("constrained_columns") == ["athlete_id"] for key in session_foreign_keys):
        connection.execute(text(
            "ALTER TABLE sessions ADD CONSTRAINT fk_sessions_athlete_id "
            "FOREIGN KEY (athlete_id) REFERENCES athletes (id) NOT VALID"
        ))
        connection.execute(text(
            "ALTER TABLE sessions VALIDATE CONSTRAINT fk_sessions_athlete_id"
        ))

    indexes = {
        "ix_athletes_coach_id": "CREATE INDEX IF NOT EXISTS ix_athletes_coach_id ON athletes (coach_id)",
        "ix_sessions_athlete_id_created_at": (
            "CREATE INDEX IF NOT EXISTS ix_sessions_athlete_id_created_at "
            "ON sessions (athlete_id, created_at DESC)"
        ),
    }
    for statement in indexes.values():
        connection.execute(text(statement))


def get_db():
    """Database dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    """Serialize PostgreSQL schema initialization across application workers."""
    if engine.dialect.name != "postgresql":
        _initialize_database()
        return

    with engine.connect() as lock_connection:
        lock_connection.execute(
            text("SELECT pg_advisory_lock(:lock_id)"),
            {"lock_id": DATABASE_INITIALIZATION_LOCK_ID},
        )
        lock_connection.commit()
        try:
            _initialize_database()
        finally:
            lock_connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": DATABASE_INITIALIZATION_LOCK_ID},
            )
            lock_connection.commit()


def _initialize_database() -> None:
    from .models.athlete import Athlete  # noqa: F401
    from .models.refresh_token import RefreshToken  # noqa: F401
    from .models.session import Session as TrainingSession  # noqa: F401
    from .models.skill import Skill  # noqa: F401
    from .models.skill_reference_pose import SkillReferencePose  # noqa: F401
    from .models.achievement import AthleteAchievement  # noqa: F401
    from .models.coach_note import CoachNote  # noqa: F401
    from .models.coach_connection_request import CoachConnectionRequest  # noqa: F401
    from .models.coach_invite import CoachInvite  # noqa: F401
    from .models.password_reset_token import PasswordResetToken  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        ensure_compatibility_columns(connection)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE athletes
                SET linked_sports = sport_type
                WHERE linked_sports IS NULL OR TRIM(linked_sports) = ''
                """
            )
        )

    # Seed default skills if none exist yet
    from .seed_data import seed_default_skills_if_empty
    from .database import SessionLocal as _SessionLocal

    with _SessionLocal() as db:
        seed_default_skills_if_empty(db)

    # Seed ideal-form reference poses (Digital Twin overlay) after skills
    # exist, since they're looked up by skill name.
    import sys
    from pathlib import Path
    backend_root = str(Path(__file__).resolve().parents[1])
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
    from seed_reference_poses import seed_reference_poses_if_empty

    with _SessionLocal() as db:
        seed_reference_poses_if_empty(db)
