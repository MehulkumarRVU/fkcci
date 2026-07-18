from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class AIGymCoachAnalyzer(BaseAnalyzer):
    def __init__(self, sport_type: str = "ai_gym_coach"):
        super().__init__(sport_type=sport_type)

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        # Frame-level hints for common exercises
        feedback = []
        technique_score = 100.0

        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        left_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_HIP"])
        right_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_HIP"])

        # Squat form check (if skill_name contains squat)
        if "Squat" in skill_name or "squat" in skill_name.lower():
            left_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_KNEE"])
            right_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_KNEE"])
            knee_angle = PoseUtils.calculate_angle(left_hip, left_knee, PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_ANKLE"]))
            if knee_angle < 140:
                feedback.append("✅ Deep squat — good range of motion.")
            else:
                feedback.append("⚠️ Not deep enough — lower hips to improve range.")
                technique_score -= 8.0

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        return {
            "score": max(0.0, technique_score * 0.6 + balance_score * 0.4),
            "technique_accuracy": technique_score,
            "balance_score": balance_score,
            "feedback": feedback,
        }

    def analyze_session(self, pose_sequence: List[List[Dict[str, float]]], skill_name: str) -> Dict[str, Any]:
        # Rep counting for simple exercises: detect knee angle troughs for squats
        angles = []
        for frame in pose_sequence:
            left_knee = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_KNEE"])
            left_hip = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_HIP"])
            left_ankle = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_ANKLE"])
            angle = PoseUtils.calculate_angle(left_hip, left_knee, left_ankle)
            angles.append(angle)

        reps = 0
        in_down = False
        for a in angles:
            if a < 140 and not in_down:
                in_down = True
            if a >= 160 and in_down:
                reps += 1
                in_down = False

        frame_results = [self.analyze_frame(frame, skill_name) for frame in pose_sequence]
        avg_score = sum(r["score"] for r in frame_results) / len(frame_results) if frame_results else 0.0

        return {
            "overall_score": round(avg_score, 2),
            "technique_accuracy": round(sum(r["technique_accuracy"] for r in frame_results) / len(frame_results), 2) if frame_results else 0.0,
            "balance_score": round(sum(r["balance_score"] for r in frame_results) / len(frame_results), 2) if frame_results else 0.0,
            "frame_count": len(frame_results),
            "detailed": {"estimated_reps": reps},
        }

    def get_supported_skills(self) -> List[str]:
        return ["Squat Form", "Push-Up Form", "Rep Counting"]
