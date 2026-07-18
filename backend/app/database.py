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
