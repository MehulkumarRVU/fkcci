from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.session import Session as SessionModel
from ..models.athlete import Athlete
from ..services.gamification_service import update_streak, check_and_award_achievements
from ..adaptive_training import AdaptiveAnalysisConfig, ACTIVE_ADAPTIVE_CATEGORIES
from .auth import get_current_athlete

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

FREE_TIER_SESSIONS_PER_30_DAYS = 5


# Pydantic Models
class SessionCreate(BaseModel):
    sport_type: str
    session_type: str  # drill / sparring / shadow / match_simulation
    skill_name: Optional[str] = None
    adaptive: Optional[AdaptiveAnalysisConfig] = None


class SessionUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_completed: Optional[bool] = None
    performance_score: Optional[float] = None
    technique_accuracy: Optional[float] = None
    reaction_score: Optional[float] = None
    balance_score: Optional[float] = None
    session_data: Optional[dict] = None
    scoring_version: Optional[str] = None
    joint_summary: Optional[dict] = None
    adaptive_mode: Optional[bool] = None
    adaptive_setup: Optional[str] = None
    adaptive_exercise: Optional[str] = None
    adaptive_reference: Optional[dict] = None


class SessionResponse(BaseModel):
    id: int
    athlete_id: int
    sport_type: str
    session_type: str
    skill_name: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: int
    is_completed: bool
    performance_score: Optional[float] = None
    technique_accuracy: Optional[float] = None
    reaction_score: Optional[float] = None
    balance_score: Optional[float] = None
    session_data: Optional[dict]
    scoring_version: Optional[str] = None
    joint_summary: Optional[dict] = None
    adaptive_mode: bool = False
    adaptive_setup: Optional[str] = None
    adaptive_exercise: Optional[str] = None
    adaptive_reference: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Routes
@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """Create a new training session"""
    from ..sports_registry import is_valid_sport

    # Validate sport type
    if not is_valid_sport(session_data.sport_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sport_type"
        )
    if session_data.adaptive and session_data.sport_type not in ACTIVE_ADAPTIVE_CATEGORIES:
        raise HTTPException(status_code=400, detail="Adaptive training is unavailable for this category")
    
    # Validate session type
    valid_session_types = ["drill", "sparring", "shadow", "match_simulation"]
    if session_data.session_type not in valid_session_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"session_type must be one of: {', '.join(valid_session_types)}"
        )

    # Free tier: capped at FREE_TIER_SESSIONS_PER_30_DAYS sessions in a
    # rolling 30-day window. Pro tier is unlimited.
    if current_athlete.membership_tier != "pro":
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_session_count = (
            db.query(SessionModel)
            .filter(SessionModel.athlete_id == current_athlete.id, SessionModel.start_time >= thirty_days_ago)
            .count()
        )
        if recent_session_count >= FREE_TIER_SESSIONS_PER_30_DAYS:
            # 402 Payment Required, not 403 - the frontend's fetchWithAuth
            # treats any 403 as an expired/invalid session and force-logs
            # the athlete out, which is wrong for a plan-limit rejection
            # (the athlete's login is completely fine).
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Free tier is limited to {FREE_TIER_SESSIONS_PER_30_DAYS} sessions per 30 days — "
                    "upgrade to Pro for unlimited sessions."
                ),
            )

    new_session = SessionModel(
        athlete_id=current_athlete.id,
        sport_type=session_data.sport_type,
        session_type=session_data.session_type,
        skill_name=session_data.skill_name,
        adaptive_mode=session_data.adaptive is not None,
        adaptive_setup=session_data.adaptive.setup if session_data.adaptive else None,
        adaptive_exercise=session_data.adaptive.exercise if session_data.adaptive else None,
        adaptive_reference=session_data.adaptive.reference.model_dump() if session_data.adaptive and session_data.adaptive.reference else None,
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session


@router.get("/", response_model=List[SessionResponse])
async def get_athlete_sessions(
    skip: int = 0,
    limit: int = 50,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """Get all sessions for the current athlete"""
    sessions = (
        db.query(SessionModel)
        .filter(SessionModel.athlete_id == current_athlete.id)
        .order_by(SessionModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """Get a specific session by ID"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Ensure the session belongs to the current athlete
    if session.athlete_id != current_athlete.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    return session


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_update: SessionUpdate,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """Update a session with performance data"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Ensure the session belongs to the current athlete
    if session.athlete_id != current_athlete.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this session"
        )
    
    # Capture completion state BEFORE applying the update - the field-update
    # loop below sets session.is_completed to the new value, so checking
    # session.is_completed afterward would always see it already True and
    # this whole block (total_sessions/performance_rating/gamification)
    # would silently never fire on a real completion.
    was_already_completed = session.is_completed

    # Update fields
    update_data = session_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)

    # If session is completed, update athlete stats
    if session_update.is_completed and not was_already_completed:
        current_athlete.total_sessions += 1
        
        # Update performance rating (weighted average)
        if current_athlete.total_sessions == 1:
            current_athlete.performance_rating = session_update.performance_score or 0
        else:
            current_athlete.performance_rating = (
                (current_athlete.performance_rating * (current_athlete.total_sessions - 1) + 
                 (session_update.performance_score or 0)) / current_athlete.total_sessions
            )
        
        current_athlete.updated_at = datetime.utcnow()

        # Gamification: streak + achievements update on the same
        # is_completed transition total_sessions/performance_rating already
        # use, so this fires exactly once per real completion.
        session_day = (session.start_time or datetime.utcnow()).date()
        update_streak(current_athlete, session_day)
        check_and_award_achievements(current_athlete, db, session)

    db.commit()
    db.refresh(session)
    
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """Delete a session"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Ensure the session belongs to the current athlete
    if session.athlete_id != current_athlete.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this session"
        )
    
    db.delete(session)
    db.commit()
    
    return None


@router.get("/stats/summary")
async def get_session_stats(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """Get session statistics summary for the current athlete"""
    sessions = db.query(SessionModel).filter(
        SessionModel.athlete_id == current_athlete.id,
        SessionModel.is_completed == True
    ).all()
    
    if not sessions:
        return {
            "total_sessions": 0,
            "total_minutes": 0,
            "average_performance": 0,
            "average_technique": 0,
            "average_reaction": 0,
            "average_balance": 0
        }
    
    total_minutes = sum(s.duration_minutes for s in sessions)
    measured_performance = [s.performance_score for s in sessions if s.performance_score is not None]
    measured_technique = [s.technique_accuracy for s in sessions if s.technique_accuracy is not None]
    measured_balance = [s.balance_score for s in sessions if s.balance_score is not None]
    avg_performance = (
        sum(measured_performance) / len(measured_performance)
        if measured_performance else None
    )
    avg_technique = (
        sum(measured_technique) / len(measured_technique)
        if measured_technique else None
    )
    # reaction_score is nullable (honest "not measured" instead of a
    # fabricated number) - average only over sessions where it was actually
    # measured rather than crashing or silently treating None as 0.
    measured_reactions = [s.reaction_score for s in sessions if s.reaction_score is not None]
    avg_reaction = sum(measured_reactions) / len(measured_reactions) if measured_reactions else None
    avg_balance = sum(measured_balance) / len(measured_balance) if measured_balance else None

    return {
        "total_sessions": len(sessions),
        "total_minutes": total_minutes,
        "average_performance": round(avg_performance, 2) if avg_performance is not None else None,
        "average_technique": round(avg_technique, 2) if avg_technique is not None else None,
        "average_reaction": round(avg_reaction, 2) if avg_reaction is not None else None,
        "average_balance": round(avg_balance, 2) if avg_balance is not None else None
    }
