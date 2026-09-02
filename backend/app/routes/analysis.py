from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from ..models.athlete import Athlete
from ..services.analysis_service import AnalysisService
from ..pose_engine.analyzer_factory import UnregisteredSportError
from .auth import get_current_athlete

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


# Pydantic Models
class PoseData(BaseModel):
    landmarks: List[Dict[str, float]]  # x, y, z, visibility for each landmark
    timestamp: float


class AnalysisRequest(BaseModel):
    sport_type: str
    skill_name: str
    pose_data: List[PoseData]
    session_id: Optional[int] = None


class AnalysisResponse(BaseModel):
    sport_type: str
    skill_name: str
    supported: bool = True
    reason: Optional[str] = None
    overall_score: Optional[float] = None
    technique_accuracy: Optional[float] = None
    balance_score: Optional[float] = None
    reaction_score: Optional[float] = None
    reaction_status: Optional[str] = None
    pose_confidence: Optional[float] = None
    calibration_status: Optional[str] = None
    feedback_messages: List[str] = []
    detailed_analysis: Dict[str, Any] = {}


class RealtimeFeedbackRequest(BaseModel):
    sport_type: str
    skill_name: str
    landmarks: List[Dict[str, float]]


def _athlete_context(current_athlete: Athlete):
    # getattr-defensive: some auth test doubles are minimal stand-ins without
    # every Athlete field populated.
    skill_level = getattr(current_athlete, "skill_level", None) or "beginner"
    dominant_hand = getattr(current_athlete, "dominant_hand", None) or "right"
    return skill_level, dominant_hand


def _validate_sport(sport_type: str):
    from ..sports_registry import is_valid_sport

    if not is_valid_sport(sport_type):
        raise HTTPException(status_code=400, detail="Invalid sport type")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_technique(
    request: AnalysisRequest,
    current_athlete: Athlete = Depends(get_current_athlete)
):
    """Analyze a full buffered pose sequence from a session.

    Calls the analyzer's analyze_session implementation (temporal smoothing,
    low-confidence frame rejection, and a real event-based reaction_score)
    instead of only averaging independent single-frame scores - previously
    this endpoint looped analyze_frame per frame and never called
    analyze_session at all, which is why sport-specific session counters
    (e.g. boxing's combination_count) were dead code.
    """
    _validate_sport(request.sport_type)

    if not request.pose_data:
        raise HTTPException(status_code=400, detail="No pose data provided")

    skill_level, dominant_hand = _athlete_context(current_athlete)
    analysis_service = AnalysisService()

    pose_sequence = [pose.landmarks for pose in request.pose_data]
    timestamps = [pose.timestamp for pose in request.pose_data]

    try:
        session_result = analysis_service.analyze_session(
            request.sport_type, request.skill_name, pose_sequence, skill_level, dominant_hand, timestamps
        )
    except UnregisteredSportError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if session_result.get("supported") is False:
        return {
            "sport_type": request.sport_type,
            "skill_name": request.skill_name,
            "supported": False,
            "reason": session_result.get("reason"),
            "feedback_messages": [],
            "detailed_analysis": {"frames_analyzed": len(pose_sequence)},
        }

    frame_results = [
        analysis_service.analyze_frame(request.sport_type, request.skill_name, pose.landmarks, skill_level, dominant_hand)
        for pose in request.pose_data
    ]

    all_feedback = []
    for result in frame_results:
        all_feedback.extend(result.get("feedback", []))
    unique_feedback = list(set(all_feedback))

    # Per-joint deviation frequency across the session - the raw material a
    # persistent athlete "digital twin" profile aggregates over time to spot
    # recurring weaknesses (e.g. "elbow deviates 'high' in 40% of sessions").
    joint_deviation_summary: Dict[str, Dict[str, int]] = {}
    for result in frame_results:
        for landmark_index, severity in (result.get("deviations") or {}).items():
            key = str(landmark_index)
            joint_deviation_summary.setdefault(key, {"low": 0, "medium": 0, "high": 0})
            joint_deviation_summary[key][severity] = joint_deviation_summary[key].get(severity, 0) + 1

    frame_scores = [r["score"] for r in frame_results if r.get("score") is not None]
    detailed = {
        "frames_analyzed": len(frame_results),
        "score_range": {
            "min": min(frame_scores) if frame_scores else None,
            "max": max(frame_scores) if frame_scores else None,
        },
        "skill_analyzed": request.skill_name,
        "joint_deviation_summary": joint_deviation_summary,
        **(session_result.get("detailed") or {}),
    }

    return {
        "sport_type": request.sport_type,
        "skill_name": request.skill_name,
        "supported": True,
        "overall_score": session_result.get("overall_score"),
        "technique_accuracy": session_result.get("technique_accuracy"),
        "balance_score": session_result.get("balance_score"),
        "reaction_score": session_result.get("reaction_score"),
        "reaction_status": session_result.get("reaction_status"),
        "pose_confidence": session_result.get("pose_confidence"),
        "calibration_status": session_result.get("calibration_status"),
        "feedback_messages": unique_feedback,
        "detailed_analysis": detailed,
    }


@router.post("/realtime-feedback")
async def get_realtime_feedback(
    request: RealtimeFeedbackRequest,
    current_athlete: Athlete = Depends(get_current_athlete)
):
    """Get instant, structured feedback for a single frame."""
    _validate_sport(request.sport_type)

    if not request.landmarks:
        raise HTTPException(status_code=400, detail="No landmarks provided")

    skill_level, dominant_hand = _athlete_context(current_athlete)
    analysis_service = AnalysisService()

    try:
        result = analysis_service.analyze_frame(
            request.sport_type, request.skill_name, request.landmarks, skill_level, dominant_hand
        )
    except UnregisteredSportError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result
