from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from ..database import Base
from ..time_utils import utc_now


class CoachNote(Base):
    """A message in a coach<->athlete conversation thread. `athlete_id`
    scopes the thread (the coached athlete); `author_id` is whoever wrote
    this particular message - either the coach or the athlete themselves -
    so this is genuinely two-way, not just a coach broadcast channel.
    `session_id` optionally scopes a note to one specific session."""
    __tablename__ = "coach_notes"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
