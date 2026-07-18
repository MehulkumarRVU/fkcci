from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class ArcheryAnalyzer(BaseAnalyzer):
    def __init__(self, sport_type: str = "indoor_archery"):
        super().__init__(sport_type=sport_type)

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        nose = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["NOSE"])

        # Alignment check: nose should be near shoulder midline when aiming
        mid_shoulder_x = (left_shoulder["x"] + right_shoulder["x"]) / 2
        if abs(nose["x"] - mid_shoulder_x) < 0.06:
            feedback.append("✅ Good head alignment with shoulders.")
        else:
            feedback.append("⚠️ Head alignment off - square shoulders to target.")
            technique_score -= 8.0

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        overall_score = max(0.0, technique_score * 0.7 + balance_score * 0.3)

        return {
            "score": overall_score,
            "technique_accuracy": max(0.0, technique_score),
            "balance_score": balance_score,
            "feedback": feedback,
        }

    def analyze_session(self, pose_sequence: List[List[Dict[str, float]]], skill_name: str) -> Dict[str, Any]:
        frame_results = [self.analyze_frame(frame, skill_name) for frame in pose_sequence]
        avg_score = sum(r["score"] for r in frame_results) / len(frame_results) if frame_results else 0.0
        return {
            "overall_score": round(avg_score, 2),
            "technique_accuracy": round(sum(r["technique_accuracy"] for r in frame_results) / len(frame_results), 2) if frame_results else 0.0,
            "balance_score": round(sum(r["balance_score"] for r in frame_results) / len(frame_results), 2) if frame_results else 0.0,
            "frame_count": len(frame_results),
        }

    def get_supported_skills(self) -> List[str]:
        return ["Draw & Anchor", "Aim Stability", "Release"]
