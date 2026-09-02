from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.thresholds import scale_penalty
from ..shared.utils import PoseUtils


class CombatAnalyzer(BaseAnalyzer):
    def __init__(self, sport_type: str = "combat"):
        super().__init__(sport_type=sport_type)

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        left_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_WRIST"])
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        left_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_HIP"])
        right_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_HIP"])

        # Guard check
        if PoseUtils.is_confident(left_shoulder) and PoseUtils.is_confident(right_shoulder) \
                and PoseUtils.is_confident(left_wrist) and PoseUtils.is_confident(right_wrist):
            avg_shoulder_y = (left_shoulder["y"] + right_shoulder["y"]) / 2
            if left_wrist["y"] < avg_shoulder_y and right_wrist["y"] < avg_shoulder_y:
                feedback.append("✅ Good guard - hands up.")
            else:
                feedback.append("❌ Guard low - keep hands protecting the face.")
                technique_score -= scale_penalty(15.0, skill_level)

        # Hip rotation hint
        if PoseUtils.is_confident(left_hip) and PoseUtils.is_confident(right_hip):
            hip_rotation = abs(left_hip["x"] - right_hip["x"])
            delta, msg = self.check_min(
                hip_rotation, 0.08, skill_level, penalty=8,
                pass_msg="✅ Adequate hip rotation for power.",
                fail_msg="⚠️ Increase hip rotation when striking.",
            )
            technique_score += delta
            feedback.append(msg)

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        technique_score = max(0.0, technique_score)
        overall_score = self.blend_scores(technique_score, balance_score, 0.65)

        return {
            "score": overall_score,
            "technique_accuracy": technique_score,
            "balance_score": balance_score,
            "feedback": feedback,
        }

    def get_supported_skills(self) -> List[str]:
        return ["Guard", "Jab", "Cross", "Kick", "Push"]
