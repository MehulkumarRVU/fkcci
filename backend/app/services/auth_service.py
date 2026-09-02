import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from sqlalchemy.orm import Session

from ..config import settings
from ..models.athlete import Athlete
from ..models.refresh_token import RefreshToken
from ..models.password_reset_token import PasswordResetToken
from ..repositories.athlete_repository import AthleteRepository

ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_DAYS = settings.ACCESS_TOKEN_EXPIRE_DAYS


class AuthService:
    def __init__(self, db: Session | None = None):
        self.db = db
        self.athlete_repo = AthleteRepository(db) if db is not None else None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            if hashed_password.startswith("$2"):
                import bcrypt

                return bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    hashed_password.encode("utf-8"),
                )

            scheme, iterations_str, salt_b64, stored_hash_b64 = hashed_password.split("$", 3)
            if scheme != "pbkdf2_sha256":
                return False

            iterations = int(iterations_str)
            salt = base64.b64decode(salt_b64.encode("utf-8"))
            stored_hash = base64.b64decode(stored_hash_b64.encode("utf-8"))

            computed_hash = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt,
                iterations,
            )
            return hmac.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False

    def get_password_hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000,
        )
        salt_b64 = base64.b64encode(salt).decode("utf-8")
        hash_b64 = base64.b64encode(password_hash).decode("utf-8")
        return f"pbkdf2_sha256$100000${salt_b64}${hash_b64}"

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, athlete: Athlete, expires_days: int = 30) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        rt = RefreshToken(
            athlete_id=athlete.id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(rt)
        self.db.commit()
        self.db.refresh(rt)
        return token

    def verify_refresh_token(self, token: str) -> Optional[RefreshToken]:
        token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        rt = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked == False)
            .first()
        )
        if not rt or rt.expires_at < datetime.utcnow():
            return None
        return rt

    def revoke_refresh_token(self, token: str) -> bool:
        token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        rt = self.db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if not rt:
            return False
        rt.revoked = True
        self.db.commit()
        return True

    def create_password_reset_token(self, athlete: Athlete, expires_minutes: int = 60) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        prt = PasswordResetToken(
            athlete_id=athlete.id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False,
        )
        self.db.add(prt)
        self.db.commit()
        self.db.refresh(prt)
        return token

    def verify_password_reset_token(self, token: str) -> Optional[PasswordResetToken]:
        token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        prt = (
            self.db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash, PasswordResetToken.used == False)
            .first()
        )
        if not prt or prt.expires_at < datetime.utcnow():
            return None
        return prt

    def consume_password_reset_token(self, token: str) -> bool:
        token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        prt = self.db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
        if not prt:
            return False
        prt.used = True
        self.db.commit()
        return True
