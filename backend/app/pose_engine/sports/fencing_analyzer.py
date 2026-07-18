from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class FencingAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="fencing")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        left_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_KNEE"])
        right_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_KNEE"])
        left_ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_ANKLE"])
        right_ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ANKLE"])
        nose = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["NOSE"])
        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])

        # Lunge depth proxy: front knee should be bent and lower than rear knee
        knee_diff = left_knee["y"] - right_knee["y"]
        if knee_diff > 0.05 or knee_diff < -0.05:
            feedback.append("✅ Lunge shows front-back leg separation.")
        else:
            feedback.append("⚠️ Lunge depth limited - increase front knee bend.")
            technique_score -= 10.0

        # Pointing arm alignment: head to shoulder to wrist roughly colinear
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        left_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_WRIST"])
        # choose side with higher wrist x distance from nose
        side = "right" if abs(right_wrist["x"] - nose["x"]) > abs(left_wrist["x"] - nose["x"]) else "left"
        wrist = right_wrist if side == "right" else left_wrist
        shoulder = right_shoulder if side == "right" else left_shoulder
        angle = PoseUtils.calculate_angle(shoulder, nose, wrist)
        if angle < 20:
            feedback.append("✅ Good arm alignment towards target.")
        else:
            feedback.append("⚠️ Adjust arm-line to point directly at target.")
            technique_score -= 8.0

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        overall_score = max(0.0, technique_score * 0.6 + balance_score * 0.4)

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
        return ["Lunge", "Parry", "Riposte", "Footwork Drill"]
