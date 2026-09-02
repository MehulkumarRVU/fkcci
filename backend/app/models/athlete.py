from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Athlete(Base):
    __tablename__ = "athletes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Role & Coach Assignment
    role = Column(String, default="athlete")  # athlete / coach
    coach_id = Column(Integer, ForeignKey("athletes.id"), nullable=True)  # Self-referential for coach assignment
    
    # Sports Profile
    sport_type = Column(String, nullable=False)  # active sport: table_tennis / boxing
    linked_sports = Column(String, default="", nullable=False)  # comma-separated enabled sports
    skill_level = Column(String, default="beginner")  # beginner / intermediate / advanced
    dominant_hand = Column(String, default="right")  # right / left
    height = Column(Float, nullable=True)  # in cm
    weight = Column(Float, nullable=True)  # in kg
    training_frequency_per_week = Column(Integer, default=0)
    
    # Membership & Performance
    membership_tier = Column(String, default="free")  # free / pro
    total_sessions = Column(Integer, default=0)
    performance_rating = Column(Float, default=0.0)  # 0-100

    # Gamification
    current_streak = Column(Integer, default=0)  # consecutive days with a completed session
    longest_streak = Column(Integer, default=0)
    last_session_date = Column(Date, nullable=True)  # date of the most recent completed session

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="athlete", cascade="all, delete-orphan")
    coached_athletes = relationship("Athlete", remote_side=[id], backref="coach")
