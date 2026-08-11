from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class FitnessAnalyzer(BaseAnalyzer):
    def __init__(self, sport_type: str = "fitness"):
        super().__init__(sport_type=sport_type)

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        left_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_HIP"])
        right_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_HIP"])

        # Torso alignment (lean). The previous 0.3 normalized-y threshold was
        # so loose relative to a shoulder-hip span it almost never triggered
        # for any real posture - tightened to a value that actually catches
        # a noticeable forward/backward lean.
        lean = None
        if PoseUtils.is_confident(left_shoulder) and PoseUtils.is_confident(right_shoulder) \
                and PoseUtils.is_confident(left_hip) and PoseUtils.is_confident(right_hip):
            shoulder_mid_x = (left_shoulder["x"] + right_shoulder["x"]) / 2
            hip_mid_x = (left_hip["x"] + right_hip["x"]) / 2
            lean = abs(shoulder_mid_x - hip_mid_x)
        delta, msg = self.check_max(
            lean, 0.08, skill_level, penalty=8,
            pass_msg="✅ Good upright torso posture.",
            fail_msg="⚠️ Adjust torso alignment to keep spine neutral.",
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
        return ["Squat Form", "Push-Up Form", "Lunge Form", "Plank Stability"]
