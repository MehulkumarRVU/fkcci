from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from ..time_utils import utc_now
from ..database import Base


class PasswordResetToken(Base):
    """A single-use, expiring password reset token. Same HMAC-hashed-token
    pattern as RefreshToken - only the hash is stored, never the raw token,
    so a leaked database dump can't be used to reset accounts."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
