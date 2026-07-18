import os
import sys
import time
import hashlib

# Ensure backend package on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database import init_database, SessionLocal
from app.routes.auth import create_refresh_token, verify_refresh_token, revoke_refresh_token
from app.models.athlete import Athlete


def test_refresh_token_hashing_and_rotation():
    init_database()
    db = SessionLocal()
    try:
        # create a test athlete
        athlete = Athlete(email="rt_test@example.com", username="rt_test", hashed_password="x", sport_type="boxing")
        db.add(athlete)
        db.commit()
        db.refresh(athlete)

        token = create_refresh_token(db, athlete, expires_days=1)
        assert token and isinstance(token, str)

        # verify the token can be found
        rt = verify_refresh_token(db, token)
        assert rt is not None
        assert rt.athlete_id == athlete.id

        # revoking should make it invalid
        revoked = revoke_refresh_token(db, token)
        assert revoked is True
        rt2 = verify_refresh_token(db, token)
        assert rt2 is None

    finally:
        # cleanup
        db.query(Athlete).filter(Athlete.username == "rt_test").delete()
        db.commit()
        db.close()
