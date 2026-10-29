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
    
    # Performance Scores (0-100). Null means the movement was not reliably
    # evaluable; zero is reserved for a measured score at the lower bound.
    performance_score = Column(Float, default=0.0)
    technique_accuracy = Column(Float, default=0.0)
    reaction_score = Column(Float, default=0.0)
    balance_score = Column(Float, default=0.0)
    
    # Detailed Data
    session_data = Column(JSON, nullable=True)  # Stores detailed analysis data

    # Which pose-scoring engine generation produced this session's scores.
    # 'v1' = pre-refactor (flat-average, no skill-level sensitivity, no
    # real reaction_score). 'v2' = shared-threshold engine with skill-level
    # tolerance, temporal smoothing, and a real fault-recovery reaction_score.
    # Lets historical scores stay distinguishable across the accuracy overhaul
    # instead of silently mixing two incomparable scoring generations.
    scoring_version = Column(String, default="v2")

    # Which skill was practiced (only sport_type was tracked before) and a
    # structured per-joint summary from the session's pose sequence - the
    # data a persistent athlete "digital twin" profile aggregates over time.
    skill_name = Column(String, nullable=True)
    joint_summary = Column(JSON, nullable=True)
    adaptive_mode = Column(Boolean, default=False, nullable=False)
    adaptive_setup = Column(String, nullable=True)
    adaptive_exercise = Column(String, nullable=True)
    adaptive_reference = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    athlete = relationship("Athlete", back_populates="sessions")
