"""Streak tracking and achievement awarding.

Achievement definitions live here as plain data (mirroring sports_registry.py's
pattern of a Python dict rather than an admin-managed table) - each entry is
checked against the athlete's current stats, and any newly-met criteria gets
a row in AthleteAchievement. Both `update_streak` and
`check_and_award_achievements` are meant to be called exactly once, from the
same place sessions.py already updates total_sessions/performance_rating -
on a session's is_completed False->True transition.
"""
from datetime import date, timedelta
from typing import List
from sqlalchemy.orm import Session as DBSession

from ..models.athlete import Athlete
from ..models.session import Session as SessionModel
from ..models.achievement import AthleteAchievement

ACHIEVEMENTS = {
    "first_session": {"name": "First Step", "description": "Complete your first training session.", "icon": "🥇"},
    "sessions_5": {"name": "Getting Started", "description": "Complete 5 training sessions.", "icon": "🎯"},
    "sessions_10": {"name": "Committed", "description": "Complete 10 training sessions.", "icon": "💪"},
    "sessions_25": {"name": "Dedicated", "description": "Complete 25 training sessions.", "icon": "🏅"},
    "sessions_50": {"name": "Veteran", "description": "Complete 50 training sessions.", "icon": "🏆"},
    "streak_7": {"name": "Week Warrior", "description": "Train 7 days in a row.", "icon": "🔥"},
    "streak_30": {"name": "Unstoppable", "description": "Train 30 days in a row.", "icon": "⚡"},
    "high_score": {"name": "Excellence", "description": "Score 95 or higher in a session.", "icon": "🌟"},
    "multi_sport": {"name": "Cross Trainer", "description": "Train in 3 or more connected sports.", "icon": "🔀"},
}


def update_streak(athlete: Athlete, session_date: date) -> None:
    """Consecutive calendar day -> +1 streak. Same day as last session ->
    no change (avoids multiple sessions in one day inflating the streak).
    A gap of more than one day -> reset to 1."""
    if athlete.last_session_date == session_date:
        return

    if athlete.last_session_date == session_date - timedelta(days=1):
        athlete.current_streak = (athlete.current_streak or 0) + 1
    else:
        athlete.current_streak = 1

    athlete.longest_streak = max(athlete.longest_streak or 0, athlete.current_streak)
    athlete.last_session_date = session_date


def check_and_award_achievements(athlete: Athlete, db: DBSession, latest_session: SessionModel) -> List[str]:
    """Checks fixed criteria against the athlete's current stats and inserts
    AthleteAchievement rows for any newly-met, not-yet-earned codes. Returns
    the list of newly-earned codes (empty if none)."""
    already_earned = {
        row.code for row in db.query(AthleteAchievement).filter(AthleteAchievement.athlete_id == athlete.id).all()
    }

    newly_earned = []

    def award(code: str):
        if code not in already_earned:
            db.add(AthleteAchievement(athlete_id=athlete.id, code=code))
            already_earned.add(code)
            newly_earned.append(code)

    if athlete.total_sessions >= 1:
        award("first_session")
    if athlete.total_sessions >= 5:
        award("sessions_5")
    if athlete.total_sessions >= 10:
        award("sessions_10")
    if athlete.total_sessions >= 25:
        award("sessions_25")
    if athlete.total_sessions >= 50:
        award("sessions_50")

    if (athlete.current_streak or 0) >= 7:
        award("streak_7")
    if (athlete.current_streak or 0) >= 30:
        award("streak_30")

    if latest_session and (latest_session.performance_score or 0) >= 95:
        award("high_score")

    linked = [s for s in (athlete.linked_sports or "").split(",") if s]
    if len(linked) >= 3:
        award("multi_sport")

    return newly_earned
