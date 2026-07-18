from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class BasketballAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="basketball")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        left_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_HIP"])
        right_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_HIP"])
        left_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_KNEE"])
        right_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_KNEE"])
        left_ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_ANKLE"])
        right_ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ANKLE"])
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        right_elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ELBOW"])

        # Shooting elbow alignment: elbow should be above wrist and near shoulder level
        if right_wrist["y"] < right_elbow["y"]:
            feedback.append("✅ Elbow/wrist alignment good for shooting.")
        else:
            feedback.append("⚠️ Adjust elbow position for better shooting form.")
            technique_score -= 8.0

        # Jump/landing symmetry check
        knee_diff = abs(left_knee["y"] - right_knee["y"])
        if knee_diff > 0.08:
            feedback.append("⚠️ Asymmetric landing - try to land evenly.")
            technique_score -= 10.0
        else:
            feedback.append("✅ Even landing mechanics.")

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
        # Provide basic jump count estimation by detecting peaks in average knee y
        knee_avgs = []
        for frame in pose_sequence:
            lk = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_KNEE"])
            rk = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["RIGHT_KNEE"])
            knee_avgs.append((lk["y"] + rk["y"]) / 2)

        jumps = 0
        for i in range(1, len(knee_avgs) - 1):
            if knee_avgs[i] < knee_avgs[i - 1] - 0.02 and knee_avgs[i] < knee_avgs[i + 1] - 0.02:
                jumps += 1

        frame_results = [self.analyze_frame(frame, skill_name) for frame in pose_sequence]
        avg_score = sum(r["score"] for r in frame_results) / len(frame_results) if frame_results else 0.0

        return {
            "overall_score": round(avg_score, 2),
            "technique_accuracy": round(sum(r["technique_accuracy"] for r in frame_results) / len(frame_results), 2) if frame_results else 0.0,
            "balance_score": round(sum(r["balance_score"] for r in frame_results) / len(frame_results), 2) if frame_results else 0.0,
            "frame_count": len(frame_results),
            "detailed": {"estimated_jumps": jumps},
        }

    def get_supported_skills(self) -> List[str]:
        return ["Jump Shot", "Layup", "Landing Mechanics", "Footwork"]
