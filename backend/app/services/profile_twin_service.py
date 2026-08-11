"""Aggregates an athlete's session history into a persistent "digital twin"
profile: score-over-time trend (overall and per sport) and recurring
joint-deviation tendencies.

Built on data this accuracy refactor introduced: real (non-fabricated)
scores, and per-session `joint_summary` deviation counts. Earlier
pre-refactor sessions still contribute real performance_score history, but
have no joint_summary, so they're naturally excluded from the joint
tendency ranking rather than needing a special case.
"""
from collections import defaultdict
from typing import Any, Dict, List

import numpy as np
from sqlalchemy.orm import Session as DBSession

from ..models.session import Session as SessionModel
from ..pose_engine.shared.utils import PoseUtils

_LANDMARK_NAMES = {index: name for name, index in PoseUtils.LANDMARKS.items()}


def _trend_direction(scores: List[float]) -> str:
    if len(scores) < 2:
        return "insufficient_data"
    x = np.arange(len(scores))
    slope = float(np.polyfit(x, scores, 1)[0])
    if slope > 0.5:
        return "improving"
    if slope < -0.5:
        return "declining"
    return "stable"


def get_athlete_twin(athlete_id: int, db: DBSession) -> Dict[str, Any]:
    sessions = (
        db.query(SessionModel)
        .filter(SessionModel.athlete_id == athlete_id, SessionModel.is_completed == True)
        .order_by(SessionModel.created_at.asc())
        .all()
    )

    if not sessions:
        return {
            "total_sessions": 0,
            "score_trend": [],
            "trend_direction": "insufficient_data",
            "per_sport": {},
            "recurring_tendencies": [],
        }

    score_trend = [
        {
            "session_id": s.id,
            "date": s.created_at.isoformat() if s.created_at else None,
            "score": s.performance_score,
            "sport_type": s.sport_type,
            "scoring_version": s.scoring_version,
        }
        for s in sessions
    ]

    per_sport_scores = defaultdict(list)
    for s in sessions:
        per_sport_scores[s.sport_type].append(s.performance_score)

    per_sport_summary = {
        sport: {
            "session_count": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2),
            "trend_direction": _trend_direction(scores),
        }
        for sport, scores in per_sport_scores.items()
    }

    # Recurring joint-deviation tendencies aggregated across sessions that
    # have a joint_summary (i.e. analyzed by the post-refactor engine).
    joint_totals: Dict[str, Dict[str, int]] = defaultdict(lambda: {"low": 0, "medium": 0, "high": 0})
    for s in sessions:
        if not s.joint_summary:
            continue
        for landmark_index, counts in s.joint_summary.items():
            for severity, count in (counts or {}).items():
                joint_totals[landmark_index][severity] = joint_totals[landmark_index].get(severity, 0) + count

    tendencies = []
    for landmark_index, counts in joint_totals.items():
        significant = counts.get("medium", 0) + counts.get("high", 0)
        if significant == 0:
            continue
        try:
            name = _LANDMARK_NAMES.get(int(landmark_index), f"landmark_{landmark_index}")
        except (TypeError, ValueError):
            name = f"landmark_{landmark_index}"
        tendencies.append({
            "joint": name.replace("_", " ").title(),
            "medium_count": counts.get("medium", 0),
            "high_count": counts.get("high", 0),
        })
    tendencies.sort(key=lambda t: (t["high_count"], t["medium_count"]), reverse=True)

    all_scores = [s.performance_score for s in sessions]

    return {
        "total_sessions": len(sessions),
        "score_trend": score_trend[-30:],  # cap payload size
        "trend_direction": _trend_direction(all_scores),
        "per_sport": per_sport_summary,
        "recurring_tendencies": tendencies[:5],
    }
