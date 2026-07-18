from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class RacketAnalyzer(BaseAnalyzer):
    def __init__(self, sport_type: str = "racket"):
        super().__init__(sport_type=sport_type)

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        # Generic racket checks: arm extension, wrist position, knee bend
        shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ELBOW"])
        wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_HIP"])
        knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_KNEE"])
        ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ANKLE"])

        arm_angle = PoseUtils.calculate_angle(shoulder, elbow, wrist)
        if arm_angle >= 140:
            feedback.append("✅ Good arm extension for racket strike.")
        elif arm_angle >= 120:
            feedback.append("⚠️ Slightly bent arm - extend more for power.")
            technique_score -= 8.0
        else:
            feedback.append("❌ Arm too bent - extend through contact.")
            technique_score -= 18.0

        knee_angle = PoseUtils.calculate_angle(hip, knee, ankle)
        if 130 <= knee_angle <= 170:
            feedback.append("✅ Stable knee bend for racket movement.")
        else:
            feedback.append("⚠️ Adjust knee bend for stability and mobility.")
            technique_score -= 6.0

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
        return ["Forehand", "Backhand", "Serve", "Volley", "Smash"]
