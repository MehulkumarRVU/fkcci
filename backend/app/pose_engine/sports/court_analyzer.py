from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class CourtAnalyzer(BaseAnalyzer):
    def __init__(self, sport_type: str = "court"):
        super().__init__(sport_type=sport_type)

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        # Jump/landing checks using knees
        left_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_KNEE"])
        right_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_KNEE"])

        knee_diff = None
        if PoseUtils.is_confident(left_knee) and PoseUtils.is_confident(right_knee):
            knee_diff = abs(left_knee["y"] - right_knee["y"])
        delta, msg = self.check_max(
            knee_diff, 0.08, skill_level, penalty=10,
            pass_msg="✅ Even leg drive/landing.",
            fail_msg="⚠️ Uneven knee bend/landing - try to land symmetrically.",
        )
        technique_score += delta
        if msg:
            feedback.append(msg)

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        technique_score = max(0.0, technique_score)
        overall_score = self.blend_scores(technique_score, balance_score, 0.6)

        return {
            "score": overall_score,
            "technique_accuracy": technique_score,
            "balance_score": balance_score,
            "feedback": feedback,
        }

    def get_supported_skills(self) -> List[str]:
        return ["Jump", "Landing", "Lateral Shuffle", "Block"]
