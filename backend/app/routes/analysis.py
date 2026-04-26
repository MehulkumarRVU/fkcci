from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from ..models.athlete import Athlete
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
    overall_score: float
    technique_accuracy: float
    balance_score: float
    feedback_messages: List[str]
    detailed_analysis: Dict[str, Any]


class RealtimeFeedbackRequest(BaseModel):
    sport_type: str
    skill_name: str
    landmarks: List[Dict[str, float]]


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_technique(
    request: AnalysisRequest,
    current_athlete: Athlete = Depends(get_current_athlete)
):
    """Analyze athlete's technique based on pose data"""
    
    if request.sport_type not in ["table_tennis", "boxing"]:
        raise HTTPException(status_code=400, detail="Invalid sport type")
    
    if not request.pose_data:
        raise HTTPException(status_code=400, detail="No pose data provided")
    
    # Import analyzer here to avoid circular imports
    from ..utils.sports_pose_analyzer import SportsPoseAnalyzer
    
    analyzer = SportsPoseAnalyzer(request.sport_type)
    
    # Analyze each frame
    frame_results = []
    for pose in request.pose_data:
        result = analyzer.analyze_frame(pose.landmarks, request.skill_name)
        frame_results.append(result)
    
    # Aggregate results
    avg_score = sum(r["score"] for r in frame_results) / len(frame_results)
    avg_technique = sum(r.get("technique_accuracy", 0) for r in frame_results) / len(frame_results)
    avg_balance = sum(r.get("balance_score", 0) for r in frame_results) / len(frame_results)
    
    # Collect unique feedback messages
    all_feedback = []
    for result in frame_results:
        all_feedback.extend(result.get("feedback", []))
    
    unique_feedback = list(set(all_feedback))
    
    # Detailed analysis
    detailed = {
        "frames_analyzed": len(frame_results),
        "score_range": {
            "min": min(r["score"] for r in frame_results),
            "max": max(r["score"] for r in frame_results),
            "avg": avg_score
        },
        "skill_analyzed": request.skill_name
    }
    
    return {
        "sport_type": request.sport_type,
        "skill_name": request.skill_name,
        "overall_score": round(avg_score, 2),
        "technique_accuracy": round(avg_technique, 2),
        "balance_score": round(avg_balance, 2),
        "feedback_messages": unique_feedback,
        "detailed_analysis": detailed
    }


@router.post("/realtime-feedback")
async def get_realtime_feedback(
    request: RealtimeFeedbackRequest,
    current_athlete: Athlete = Depends(get_current_athlete)
):
    """Get instant feedback for a single frame"""
    
    if request.sport_type not in ["table_tennis", "boxing"]:
        raise HTTPException(status_code=400, detail="Invalid sport type")

    if not request.landmarks:
        raise HTTPException(status_code=400, detail="No landmarks provided")
    
    from ..utils.sports_pose_analyzer import SportsPoseAnalyzer
    
    analyzer = SportsPoseAnalyzer(request.sport_type)
    result = analyzer.analyze_frame(request.landmarks, request.skill_name)
    
    return result
