from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from ..database import Base


class CoachInvite(Base):
    """A coach-generated, shareable join code. An athlete redeeming a valid
    (non-revoked) code connects immediately - sharing the code is itself the
    coach's consent, unlike the CoachConnectionRequest accept/reject flow."""
    __tablename__ = "coach_invites"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Boolean, default=False)
