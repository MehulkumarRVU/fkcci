from typing import Any, Dict, List, Optional
from ..base_analyzer import BaseAnalyzer
from ..shared.thresholds import scale_penalty
from ..shared.utils import PoseUtils


class BasketballAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="basketball")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        left_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_KNEE"])
        right_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_KNEE"])
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        right_elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ELBOW"])

        # Shooting elbow alignment: elbow should be above wrist
        if PoseUtils.is_confident(right_wrist) and PoseUtils.is_confident(right_elbow):
            if right_wrist["y"] < right_elbow["y"]:
                feedback.append("✅ Elbow/wrist alignment good for shooting.")
            else:
                feedback.append("⚠️ Adjust elbow position for better shooting form.")
                technique_score -= scale_penalty(8.0, skill_level)

        # Jump/landing symmetry check
        knee_diff = None
        if PoseUtils.is_confident(left_knee) and PoseUtils.is_confident(right_knee):
            knee_diff = abs(left_knee["y"] - right_knee["y"])
        delta, msg = self.check_max(
            knee_diff, 0.08, skill_level, penalty=10,
            pass_msg="✅ Even landing mechanics.",
            fail_msg="⚠️ Asymmetric landing - try to land evenly.",
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

    def analyze_session(self, pose_sequence: List[List[Dict[str, float]]], skill_name: str,
                         skill_level: str = "beginner", dominant_hand: str = "right",
                         timestamps: Optional[List[float]] = None) -> Dict[str, Any]:
        result = super().analyze_session(pose_sequence, skill_name, skill_level, dominant_hand, timestamps)

        # Basic jump count estimation by detecting peaks (troughs in y) in
        # average knee height.
        knee_avgs = []
        for frame in pose_sequence:
            lk = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_KNEE"])
            rk = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["RIGHT_KNEE"])
            knee_avgs.append((lk["y"] + rk["y"]) / 2)

        jumps = 0
        for i in range(1, len(knee_avgs) - 1):
            if knee_avgs[i] < knee_avgs[i - 1] - 0.02 and knee_avgs[i] < knee_avgs[i + 1] - 0.02:
                jumps += 1

        result["detailed"] = {"estimated_jumps": jumps}
        return result

    def get_supported_skills(self) -> List[str]:
        return ["Jump Shot", "Layup", "Landing Mechanics", "Footwork"]
