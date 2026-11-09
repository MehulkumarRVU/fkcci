import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import secrets
from datetime import timedelta
from threading import BoundedSemaphore
from typing import Callable, Optional, TypeVar

from jose import jwt
from sqlalchemy.orm import Session

from ..config import settings
from ..models.athlete import Athlete
from ..models.refresh_token import RefreshToken
from ..models.password_reset_token import PasswordResetToken
from ..repositories.athlete_repository import AthleteRepository
from ..time_utils import as_utc, utc_now

ALGORITHM = settings.ALGORITHM
PASSWORD_HASH_MAX_IN_FLIGHT = 256
_password_hash_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="password-hash",
)
_password_hash_capacity = BoundedSemaphore(PASSWORD_HASH_MAX_IN_FLIGHT)
_Result = TypeVar("_Result")


class PasswordHashCapacityExceeded(Exception):
    """Raised when the bounded password-hash queue is full."""


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

    async def _run_password_operation(
        self,
        operation: Callable[..., _Result],
        *args: str,
    ) -> _Result:
        loop = asyncio.get_running_loop()
        capacity = _password_hash_capacity
        if not capacity.acquire(blocking=False):
            raise PasswordHashCapacityExceeded

        try:
            future = _password_hash_executor.submit(operation, *args)
        except Exception:
            capacity.release()
            raise

        future.add_done_callback(lambda _: capacity.release())
        return await asyncio.shield(asyncio.wrap_future(future, loop=loop))

    async def get_password_hash_async(self, password: str) -> str:
        return await self._run_password_operation(self.get_password_hash, password)

    async def verify_password_async(
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        return await self._run_password_operation(
            self.verify_password,
            plain_password,
            hashed_password,
        )

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        issued_at = utc_now()
        max_lifetime = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        lifetime = min(expires_delta, max_lifetime) if expires_delta else max_lifetime
        to_encode.update({"iat": issued_at, "exp": issued_at + lifetime})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, athlete: Athlete, expires_days: int = 30) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        expires_at = utc_now() + timedelta(days=expires_days)
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
        if not rt or as_utc(rt.expires_at) < utc_now():
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

    def rotate_refresh_token(self, token: str, athlete: Athlete) -> Optional[str]:
        rt = self.verify_refresh_token(token)
        if rt is None or rt.athlete_id != athlete.id:
            return None

        updated = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.id == rt.id, RefreshToken.revoked == False)
            .update({RefreshToken.revoked: True}, synchronize_session=False)
        )
        if updated != 1:
            self.db.rollback()
            return None

        new_token = secrets.token_urlsafe(32)
        token_hash = hmac.new(
            settings.SECRET_KEY.encode(), new_token.encode(), hashlib.sha256
        ).hexdigest()
        self.db.add(
            RefreshToken(
                athlete_id=athlete.id,
                token_hash=token_hash,
                expires_at=utc_now() + timedelta(days=30),
                revoked=False,
            )
        )
        self.db.commit()
        return new_token

    def create_password_reset_token(self, athlete: Athlete, expires_minutes: int = 60) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        expires_at = utc_now() + timedelta(minutes=expires_minutes)
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
        if not prt or as_utc(prt.expires_at) < utc_now():
            return None
        return prt

    def consume_password_reset_token(self, token: str) -> bool:
        token_hash = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
        updated = (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > utc_now(),
            )
            .update(
                {PasswordResetToken.used: True},
                synchronize_session=False,
            )
        )
        if updated != 1:
            self.db.rollback()
            return False
        self.db.commit()
        return True
