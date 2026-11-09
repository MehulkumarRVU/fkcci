from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.session import Session as SessionModel
from ..models.athlete import Athlete
from ..services.profile_twin_service import get_athlete_twin
from .auth import get_current_athlete
from ..time_utils import as_utc, utc_now

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/me/profile-twin")
def get_my_profile_twin(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """The athlete's persistent 'digital twin': score-over-time trend and
    recurring joint-deviation tendencies aggregated across their session
    history."""
    return get_athlete_twin(current_athlete.id, db)


# Pydantic Models
class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    athlete_username: str
    sport_type: str
    session_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: int
    is_completed: bool
    performance_score: float
    technique_accuracy: float
    reaction_score: Optional[float] = None
    balance_score: float

class MonthlyStats(BaseModel):
    athlete_id: int
    athlete_username: str
    total_sessions: int
    completed_sessions: int
    avg_performance_score: float
    avg_technique_accuracy: float
    avg_reaction_score: Optional[float] = None
    avg_balance_score: float
    highest_performance: float
    lowest_performance: float
    total_training_hours: int


class AthleteReport(BaseModel):
    athlete_id: int
    athlete_username: str
    skill_level: str
    sport_type: str
    linked_sports: List[str]
    total_sessions: int
    this_month_sessions: int
    performance_rating: float
    monthly_stats: MonthlyStats
    recent_sessions: List[SessionSummary]


# Routes
@router.get("/coach/athletes", response_model=List[dict])
def get_coach_athletes(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """Get all athletes coached by the current coach"""
    if current_athlete.role != "coach":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only coaches can access this endpoint"
        )

    athletes = db.query(Athlete).filter(
        Athlete.coach_id == current_athlete.id,
        Athlete.role == "athlete"
    ).all()

    return [
        {
            "id": athlete.id,
            "username": athlete.username,
            "email": athlete.email,
            "skill_level": athlete.skill_level,
            "sport_type": athlete.sport_type,
            "linked_sports": athlete.linked_sports.split(',') if athlete.linked_sports else [],
            "created_at": athlete.created_at
        }
        for athlete in athletes
    ]


def build_athlete_monthly_report(athlete_id: int, current_athlete: Athlete, db: Session) -> AthleteReport:
    """Shared data-gathering for the monthly report - used by both the JSON
    endpoint below and the coach PDF export route, so the 30-day aggregation
    logic exists in exactly one place."""
    if current_athlete.role != "coach":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only coaches can access this endpoint"
        )

    athlete = db.query(Athlete).filter(Athlete.id == athlete_id).first()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found"
        )

    # Check if this athlete is coached by the current coach
    if athlete.coach_id != current_athlete.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this athlete's data"
        )

    # Get all sessions for this athlete
    all_sessions = db.query(SessionModel).filter(
        SessionModel.athlete_id == athlete_id
    ).order_by(SessionModel.created_at.desc()).all()

    # Filter sessions from past 30 days
    thirty_days_ago = utc_now() - timedelta(days=30)
    recent_sessions = [s for s in all_sessions if as_utc(s.created_at) >= thirty_days_ago]

    # Calculate monthly statistics
    completed_sessions = [s for s in recent_sessions if s.is_completed]

    if completed_sessions:
        avg_perf = sum(s.performance_score for s in completed_sessions) / len(completed_sessions)
        avg_tech = sum(s.technique_accuracy for s in completed_sessions) / len(completed_sessions)
        # reaction_score is nullable (honest "not measured" instead of a
        # fabricated number) - average only over sessions where it was
        # actually measured.
        measured_reactions = [s.reaction_score for s in completed_sessions if s.reaction_score is not None]
        avg_react = sum(measured_reactions) / len(measured_reactions) if measured_reactions else None
        avg_balance = sum(s.balance_score for s in completed_sessions) / len(completed_sessions)
        highest_perf = max(s.performance_score for s in completed_sessions)
        lowest_perf = min(s.performance_score for s in completed_sessions)
        total_hours = sum(s.duration_minutes or 0 for s in completed_sessions) // 60
    else:
        avg_perf = avg_tech = avg_react = avg_balance = 0.0
        highest_perf = lowest_perf = 0.0
        total_hours = 0

    monthly_stats = MonthlyStats(
        athlete_id=athlete_id,
        athlete_username=athlete.username,
        total_sessions=len(recent_sessions),
        completed_sessions=len(completed_sessions),
        avg_performance_score=round(avg_perf, 2),
        avg_technique_accuracy=round(avg_tech, 2),
        avg_reaction_score=round(avg_react, 2) if avg_react is not None else None,
        avg_balance_score=round(avg_balance, 2),
        highest_performance=round(highest_perf, 2),
        lowest_performance=round(lowest_perf, 2),
        total_training_hours=total_hours
    )

    # Get summary of recent 10 sessions
    recent_summary = [
        SessionSummary(
            id=s.id,
            athlete_username=athlete.username,
            sport_type=s.sport_type,
            session_type=s.session_type,
            start_time=s.start_time,
            end_time=s.end_time,
            duration_minutes=s.duration_minutes or 0,
            is_completed=s.is_completed,
            performance_score=s.performance_score,
            technique_accuracy=s.technique_accuracy,
            reaction_score=s.reaction_score,
            balance_score=s.balance_score
        )
        for s in recent_sessions[:10]
    ]

    return AthleteReport(
        athlete_id=athlete_id,
        athlete_username=athlete.username,
        skill_level=athlete.skill_level,
        sport_type=athlete.sport_type,
        linked_sports=athlete.linked_sports.split(',') if athlete.linked_sports else [],
        total_sessions=len(all_sessions),
        this_month_sessions=len(recent_sessions),
        performance_rating=athlete.performance_rating,
        monthly_stats=monthly_stats,
        recent_sessions=recent_summary
    )


@router.get("/coach/athlete/{athlete_id}/monthly-report", response_model=AthleteReport)
def get_athlete_monthly_report(
    athlete_id: int,
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """Get detailed monthly report for an athlete (coach only)"""
    return build_athlete_monthly_report(athlete_id, current_athlete, db)


@router.get("/coach/summary")
def get_coach_summary(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """Get overall summary of all coached athletes"""
    if current_athlete.role != "coach":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only coaches can access this endpoint"
        )

    coached_athletes = db.query(Athlete).filter(
        Athlete.coach_id == current_athlete.id,
        Athlete.role == "athlete"
    ).all()

    athlete_ids = [a.id for a in coached_athletes]
    
    if not athlete_ids:
        return {
            "total_athletes": 0,
            "total_sessions_this_month": 0,
            "avg_performance_across_athletes": 0.0,
            "most_active_athlete": None,
            "top_performers": []
        }

    thirty_days_ago = utc_now() - timedelta(days=30)
    
    # Get statistics for all athletes
    monthly_sessions = db.query(SessionModel).filter(
        SessionModel.athlete_id.in_(athlete_ids),
        SessionModel.created_at >= thirty_days_ago
    ).all()

    completed = [s for s in monthly_sessions if s.is_completed]
    avg_performance = sum(s.performance_score for s in completed) / len(completed) if completed else 0

    # Find most active athlete
    session_counts = {}
    for s in monthly_sessions:
        session_counts[s.athlete_id] = session_counts.get(s.athlete_id, 0) + 1
    
    most_active_id = max(session_counts, key=session_counts.get) if session_counts else None
    most_active = None
    if most_active_id:
        athlete = db.query(Athlete).filter(Athlete.id == most_active_id).first()
        most_active = {"username": athlete.username, "sessions": session_counts[most_active_id]}

    # Get top performers
    athlete_avg_scores = {}
    for athlete_id in athlete_ids:
        athlete_sessions = [s for s in monthly_sessions if s.athlete_id == athlete_id and s.is_completed]
        if athlete_sessions:
            avg_score = sum(s.performance_score for s in athlete_sessions) / len(athlete_sessions)
            athlete_avg_scores[athlete_id] = avg_score

    top_performers = []
    for athlete_id, avg_score in sorted(athlete_avg_scores.items(), key=lambda x: x[1], reverse=True)[:5]:
        athlete = db.query(Athlete).filter(Athlete.id == athlete_id).first()
        top_performers.append({
            "username": athlete.username,
            "avg_performance": round(avg_score, 2)
        })

    return {
        "total_athletes": len(coached_athletes),
        "total_sessions_this_month": len(monthly_sessions),
        "completed_sessions_this_month": len(completed),
        "avg_performance_across_athletes": round(avg_performance, 2),
        "most_active_athlete": most_active,
        "top_performers": top_performers
    }
