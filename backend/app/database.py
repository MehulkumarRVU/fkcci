from pathlib import Path
from sqlalchemy import create_engine, text
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


def get_db():
    """Database dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    """Initialize database tables and compatibility columns."""
    from .models.athlete import Athlete  # noqa: F401
    from .models.refresh_token import RefreshToken  # noqa: F401
    from .models.session import Session as TrainingSession  # noqa: F401
    from .models.skill import Skill  # noqa: F401
    from .models.skill_reference_pose import SkillReferencePose  # noqa: F401
    from .models.achievement import AthleteAchievement  # noqa: F401
    from .models.coach_note import CoachNote  # noqa: F401

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(athletes)")).fetchall()
        column_names = {column[1] for column in columns}

        if "linked_sports" not in column_names:
            connection.execute(text("ALTER TABLE athletes ADD COLUMN linked_sports VARCHAR DEFAULT '' NOT NULL"))

        if "role" not in column_names:
            connection.execute(text("ALTER TABLE athletes ADD COLUMN role VARCHAR DEFAULT 'athlete' NOT NULL"))

        if "coach_id" not in column_names:
            connection.execute(text("ALTER TABLE athletes ADD COLUMN coach_id INTEGER"))

        if "current_streak" not in column_names:
            connection.execute(text("ALTER TABLE athletes ADD COLUMN current_streak INTEGER DEFAULT 0"))

        if "longest_streak" not in column_names:
            connection.execute(text("ALTER TABLE athletes ADD COLUMN longest_streak INTEGER DEFAULT 0"))

        if "last_session_date" not in column_names:
            connection.execute(text("ALTER TABLE athletes ADD COLUMN last_session_date DATE"))

        connection.execute(
            text(
                """
                UPDATE athletes
                SET linked_sports = sport_type
                WHERE linked_sports IS NULL OR TRIM(linked_sports) = ''
                """
            )
        )

        session_columns = connection.execute(text("PRAGMA table_info(sessions)")).fetchall()
        session_column_names = {column[1] for column in session_columns}

        if "scoring_version" not in session_column_names:
            connection.execute(text("ALTER TABLE sessions ADD COLUMN scoring_version VARCHAR DEFAULT 'v1'"))

        if "skill_name" not in session_column_names:
            connection.execute(text("ALTER TABLE sessions ADD COLUMN skill_name VARCHAR"))

        if "joint_summary" not in session_column_names:
            connection.execute(text("ALTER TABLE sessions ADD COLUMN joint_summary TEXT"))

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
