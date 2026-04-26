from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./pocketcoach.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Database dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Initialize database and create all tables"""
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
