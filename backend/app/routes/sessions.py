from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.session import Session as SessionModel
from ..models.athlete import Athlete
from .auth import get_current_athlete

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


# Pydantic Models
class SessionCreate(BaseModel):
    sport_type: str
    session_type: str  # drill / sparring / shadow / match_simulation


class SessionUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_completed: Optional[bool] = None
    performance_score: Optional[float] = None
    technique_accuracy: Optional[float] = None
    reaction_score: Optional[float] = None
    balance_score: Optional[float] = None
    session_data: Optional[dict] = None


class SessionResponse(BaseModel):
    id: int
    athlete_id: int
    sport_type: str
    session_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: int
    is_completed: bool
    performance_score: float
    technique_accuracy: float
    reaction_score: float
    balance_score: float
    session_data: Optional[dict]
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
    
    # Validate session type
    valid_session_types = ["drill", "sparring", "shadow", "match_simulation"]
    if session_data.session_type not in valid_session_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"session_type must be one of: {', '.join(valid_session_types)}"
        )
    
    new_session = SessionModel(
        athlete_id=current_athlete.id,
        sport_type=session_data.sport_type,
        session_type=session_data.session_type
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
    
    # Update fields
    update_data = session_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)
    
    # If session is completed, update athlete stats
    if session_update.is_completed and not session.is_completed:
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
    avg_performance = sum(s.performance_score for s in sessions) / len(sessions)
    avg_technique = sum(s.technique_accuracy for s in sessions) / len(sessions)
    avg_reaction = sum(s.reaction_score for s in sessions) / len(sessions)
    avg_balance = sum(s.balance_score for s in sessions) / len(sessions)
    
    return {
        "total_sessions": len(sessions),
        "total_minutes": total_minutes,
        "average_performance": round(avg_performance, 2),
        "average_technique": round(avg_technique, 2),
        "average_reaction": round(avg_reaction, 2),
        "average_balance": round(avg_balance, 2)
    }
