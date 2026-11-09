from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from ..database import Base
from ..time_utils import utc_now


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    sport_type = Column(String, nullable=False)  # table_tennis / boxing
    description = Column(Text, nullable=True)
    
    # Guidance
    technique_tips = Column(Text, nullable=True)
    common_mistakes = Column(Text, nullable=True)
    safety_warning = Column(Text, nullable=True)
    
    # Classification
    difficulty_level = Column(String, default="beginner")  # beginner / intermediate / advanced
    primary_focus = Column(String, nullable=True)  # power / speed / accuracy / defense
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
