from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    
    # Session Info
    sport_type = Column(String, nullable=False)  # table_tennis / boxing
    session_type = Column(String, nullable=False)  # drill / sparring / shadow / match_simulation
    
    # Timing
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    
    # Performance Scores (0-100)
    performance_score = Column(Float, default=0.0)
    technique_accuracy = Column(Float, default=0.0)
    reaction_score = Column(Float, default=0.0)
    balance_score = Column(Float, default=0.0)
    
    # Detailed Data
    session_data = Column(JSON, nullable=True)  # Stores detailed analysis data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    athlete = relationship("Athlete", back_populates="sessions")
