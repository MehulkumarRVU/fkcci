from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models.athlete import Athlete
from ..models.achievement import AthleteAchievement
from ..services.gamification_service import ACHIEVEMENTS
from .auth import get_current_athlete

router = APIRouter(prefix="/api/gamification", tags=["Gamification"])


class AchievementOut(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    earned_at: datetime


class GamificationSummary(BaseModel):
    current_streak: int
    longest_streak: int
    achievements: List[AchievementOut]
    total_available: int


@router.get("/me", response_model=GamificationSummary)
async def get_my_gamification(
    current_athlete: Athlete = Depends(get_current_athlete),
    db: Session = Depends(get_db)
):
    """The current athlete's streak and earned achievements."""
    earned = (
        db.query(AthleteAchievement)
        .filter(AthleteAchievement.athlete_id == current_athlete.id)
        .order_by(AthleteAchievement.earned_at.desc())
        .all()
    )

    achievements = [
        AchievementOut(
            code=row.code,
            name=ACHIEVEMENTS.get(row.code, {}).get("name", row.code),
            description=ACHIEVEMENTS.get(row.code, {}).get("description", ""),
            icon=ACHIEVEMENTS.get(row.code, {}).get("icon", "🏅"),
            earned_at=row.earned_at,
        )
        for row in earned
    ]

    return GamificationSummary(
        current_streak=current_athlete.current_streak or 0,
        longest_streak=current_athlete.longest_streak or 0,
        achievements=achievements,
        total_available=len(ACHIEVEMENTS),
    )
