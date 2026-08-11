from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from ..database import Base


class CoachConnectionRequest(Base):
    """An athlete-initiated request to connect with a coach (the
    search-and-request path). The coach-invite-code path (CoachInvite)
    connects athletes directly without going through this pending state,
    since generating and sharing a code is itself the coach's consent."""
    __tablename__ = "coach_connection_requests"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    status = Column(String, default="pending")  # pending / accepted / rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
