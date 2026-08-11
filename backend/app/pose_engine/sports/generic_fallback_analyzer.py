from typing import Any, Dict, List, Optional
from ..base_analyzer import BaseAnalyzer


class GenericFallbackAnalyzer(BaseAnalyzer):
    """Honest fallback for sports registered in sports_registry.py that don't
    have a tuned pose analyzer yet (or, for motogp/formula1, never will -
    seated/helmeted/vehicle-occluded activities aren't assessable via webcam
    pose analysis at all).

    Never fabricates a score by borrowing an unrelated analyzer's logic
    (e.g. scoring kabaddi against boxing's guard-position heuristics) and
    never crashes with an uncaught ValueError -> 500. Instead it reports
    `supported: false` with a plain-language reason so callers can show
    "coaching for this sport isn't available yet" honestly.
    """

    def __init__(self, sport_type: str, reason: str = "not_yet_implemented"):
        super().__init__(sport_type=sport_type)
        self.reason = reason

    def _message(self) -> str:
        if self.reason == "not_pose_coachable":
            return "ℹ️ This activity can't be assessed via webcam pose analysis."
        return "ℹ️ Coaching for this sport isn't available yet - check back soon."

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        return {
            "supported": False,
            "reason": self.reason,
            "score": None,
            "technique_accuracy": None,
            "balance_score": None,
            "reaction_score": None,
            "reaction_status": "not_measured",
            "pose_confidence": None,
            "calibration_status": "unsupported",
            "feedback": [self._message()],
            "joint_angles": {},
        }

    def analyze_session(self, pose_sequence: List[List[Dict[str, float]]], skill_name: str,
                         skill_level: str = "beginner", dominant_hand: str = "right",
                         timestamps: Optional[List[float]] = None) -> Dict[str, Any]:
        return {
            "supported": False,
            "reason": self.reason,
            "overall_score": None,
            "technique_accuracy": None,
            "balance_score": None,
            "reaction_score": None,
            "reaction_status": "not_measured",
            "pose_confidence": None,
            "calibration_status": "unsupported",
            "frame_count": len(pose_sequence) if pose_sequence else 0,
        }

    def get_supported_skills(self) -> List[str]:
        return []
