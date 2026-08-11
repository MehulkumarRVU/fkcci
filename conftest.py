import os
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Use a temporary file-backed database for tests and ensure a valid secret key.
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pocketcoach")
os.environ.setdefault("REDIS_URL", "")
# The main app's RateLimitMiddleware instance (and its in-memory bucket) is
# created once and shared across the whole pytest session since conftest
# imports `backend.main.app` a single time - cumulative requests from the
# growing test suite were tripping the default 60-req/60s limit well before
# any individual test misbehaved. test_rate_limit.py/test_rate_limit_redis.py
# build their own isolated app + middleware instance with explicit limits,
# so raising this ambient default doesn't weaken what they test.
os.environ.setdefault("RATE_LIMIT_REQUESTS", "5000")

import tempfile

temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{temp_db.name}")

from backend.app.database import Base, engine, init_database
from backend.main import app as fastapi_app


@pytest.fixture(scope="session", autouse=True)
def ensure_database_initialized():
    init_database()
    yield


@pytest.fixture(scope="function", autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def app():
    return fastapi_app


@pytest.fixture(scope="function")
def client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    from backend.app.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
