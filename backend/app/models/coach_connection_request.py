from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from ..database import Base
from ..time_utils import utc_now


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
    created_at = Column(DateTime(timezone=True), default=utc_now)
    responded_at = Column(DateTime(timezone=True), nullable=True)
