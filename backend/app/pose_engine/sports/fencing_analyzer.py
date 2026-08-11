from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.thresholds import scale_penalty
from ..shared.utils import PoseUtils


class FencingAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="fencing")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        left_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_KNEE"])
        right_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_KNEE"])
        nose = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["NOSE"])
        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        left_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_WRIST"])

        # Lunge depth proxy: front knee should be bent and lower than rear knee
        if PoseUtils.is_confident(left_knee) and PoseUtils.is_confident(right_knee):
            knee_diff = left_knee["y"] - right_knee["y"]
            if abs(knee_diff) > 0.05:
                feedback.append("✅ Lunge shows front-back leg separation.")
            else:
                feedback.append("⚠️ Lunge depth limited - increase front knee bend.")
                technique_score -= scale_penalty(10.0, skill_level)

        # Pointing arm alignment: head to shoulder to wrist roughly colinear
        if PoseUtils.is_confident(nose) and PoseUtils.is_confident(right_wrist) and PoseUtils.is_confident(left_wrist):
            side = "right" if abs(right_wrist["x"] - nose["x"]) > abs(left_wrist["x"] - nose["x"]) else "left"
            wrist = right_wrist if side == "right" else left_wrist
            shoulder = right_shoulder if side == "right" else left_shoulder
            angle = PoseUtils.calculate_angle_safe(shoulder, nose, wrist)
            delta, msg = self.check_max(
                angle, 20, skill_level, penalty=8,
                pass_msg="✅ Good arm alignment towards target.",
                fail_msg="⚠️ Adjust arm-line to point directly at target.",
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
        return ["Lunge", "Parry", "Riposte", "Footwork Drill"]
