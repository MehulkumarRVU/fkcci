from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from ..database import Base
from ..time_utils import utc_now


class AthleteAchievement(Base):
    """An earned achievement. Definitions (name/description/icon/criteria)
    live in code (app/services/gamification_service.py), mirroring the
    Python-dict pattern sports_registry.py already uses for sport metadata,
    rather than a separate admin-managed table - `code` is the only link
    back to a definition."""
    __tablename__ = "athlete_achievements"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    code = Column(String, nullable=False)
    earned_at = Column(DateTime(timezone=True), default=utc_now)
