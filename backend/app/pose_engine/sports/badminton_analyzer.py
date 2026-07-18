from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class BadmintonAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="badminton")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        feedback = []
        joint_angles = {}
        technique_score = 100.0

        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        right_elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ELBOW"])
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        left_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_HIP"])
        left_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_KNEE"])
        left_ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_ANKLE"])

        if "Serve" in skill_name or "Clear" in skill_name or "Smash" in skill_name:
            arm_angle = PoseUtils.calculate_angle(right_shoulder, right_elbow, right_wrist)
            joint_angles["arm_extension"] = arm_angle
            if arm_angle >= 150:
                feedback.append("✅ Strong extension and reach.")
            elif arm_angle >= 130:
                feedback.append("⚠️ Good extension, keep the arm straighter for more power.")
                technique_score -= 10.0
            else:
                feedback.append("❌ Arm too bent - extend more through the shot.")
                technique_score -= 20.0

        if "Footwork" in skill_name or "Movement" in skill_name:
            knee_angle = PoseUtils.calculate_angle(left_hip, left_knee, left_ankle)
            joint_angles["knee_bend"] = knee_angle
            if 140 <= knee_angle <= 170:
                feedback.append("✅ Good knee bend for quick badminton footwork.")
            elif knee_angle < 140:
                feedback.append("⚠️ Slightly bend your knees more for better balance.")
                technique_score -= 10.0
            else:
                feedback.append("⚠️ Avoid over-bending and losing mobility.")
                technique_score -= 5.0

        if "Net Play" in skill_name:
            if right_wrist["y"] < right_elbow["y"]:
                feedback.append("✅ Good wrist position for net control.")
            else:
                feedback.append("⚠️ Keep your racket hand higher for delicate net shots.")
                technique_score -= 10.0

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        overall_score = max(0.0, technique_score * 0.65 + balance_score * 0.35)

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
            "Serve Technique",
            "Clear",
            "Smash",
            "Drop Shot",
            "Net Play",
            "Split Step Footwork",
            "Defensive Block",
        ]
