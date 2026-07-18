from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class TableTennisAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="table_tennis")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        feedback = []
        joint_angles = {}
        technique_score = 100.0

        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        right_elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ELBOW"])
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        right_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_HIP"])
        right_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_KNEE"])
        right_ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ANKLE"])

        arm_angle = PoseUtils.calculate_angle(right_shoulder, right_elbow, right_wrist)
        joint_angles["arm_extension"] = arm_angle
        if "Drive" in skill_name or "Topspin" in skill_name:
            if 130 <= arm_angle <= 170:
                feedback.append("✅ Good arm extension.")
            elif arm_angle < 130:
                feedback.append("❌ Elbow too bent - extend more.")
                technique_score -= 15.0
            else:
                feedback.append("⚠️ Arm too straight - slight bend needed.")
                technique_score -= 10.0

        knee_angle = PoseUtils.calculate_angle(right_hip, right_knee, right_ankle)
        joint_angles["knee_flexion"] = knee_angle
        if 140 <= knee_angle <= 170:
            feedback.append("✅ Good knee bend for stability.")
        elif knee_angle < 140:
            feedback.append("⚠️ Too much knee bend - raise up slightly.")
            technique_score -= 10.0
        else:
            feedback.append("❌ Insufficient knee bend - lower your stance.")
            technique_score -= 15.0

        if right_elbow["y"] > right_shoulder["y"] + 0.1:
            feedback.append("❌ Elbow too low - keep it up.")
            technique_score -= 15.0

        if "Topspin" in skill_name:
            if right_wrist["y"] < right_elbow["y"]:
                feedback.append("✅ Good wrist position for topspin.")
            else:
                feedback.append("⚠️ Wrist should be higher than elbow for topspin.")
                technique_score -= 10.0

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        overall_score = max(0.0, technique_score * 0.7 + balance_score * 0.3)

        return {
            "score": overall_score,
            "technique_accuracy": max(0.0, technique_score),
            "balance_score": balance_score,
            "feedback": feedback,
            "joint_angles": joint_angles,
        }

    def analyze_session(self, pose_sequence: List[List[Dict[str, float]]], skill_name: str) -> Dict[str, Any]:
        frame_results = [self.analyze_frame(frame, skill_name) for frame in pose_sequence]
        avg_score = sum(r["score"] for r in frame_results) / len(frame_results) if frame_results else 0.0
        avg_tech = sum(r["technique_accuracy"] for r in frame_results) / len(frame_results) if frame_results else 0.0
        avg_balance = sum(r["balance_score"] for r in frame_results) / len(frame_results) if frame_results else 0.0
        return {
            "overall_score": round(avg_score, 2),
            "technique_accuracy": round(avg_tech, 2),
            "balance_score": round(avg_balance, 2),
            "frame_count": len(frame_results),
        }

    def get_supported_skills(self) -> List[str]:
        return [
            "Forehand Drive",
            "Backhand Drive",
            "Topspin",
            "Backspin",
            "Serve Technique",
            "Side Shuffle Footwork",
            "Smash",
        ]
