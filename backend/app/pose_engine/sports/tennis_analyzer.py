from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class TennisAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="tennis")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        # Use right-side landmarks for racket hand; fall back to left if visibility low
        rs = PoseUtils.LANDMARKS
        right_shoulder = PoseUtils.get_landmark(landmarks, rs["RIGHT_SHOULDER"])
        right_elbow = PoseUtils.get_landmark(landmarks, rs["RIGHT_ELBOW"])
        right_wrist = PoseUtils.get_landmark(landmarks, rs["RIGHT_WRIST"])
        left_shoulder = PoseUtils.get_landmark(landmarks, rs["LEFT_SHOULDER"])
        left_elbow = PoseUtils.get_landmark(landmarks, rs["LEFT_ELBOW"])
        left_wrist = PoseUtils.get_landmark(landmarks, rs["LEFT_WRIST"])
        nose = PoseUtils.get_landmark(landmarks, rs["NOSE"])
        left_hip = PoseUtils.get_landmark(landmarks, rs["LEFT_HIP"])
        right_hip = PoseUtils.get_landmark(landmarks, rs["RIGHT_HIP"])
        left_knee = PoseUtils.get_landmark(landmarks, rs["LEFT_KNEE"])
        right_knee = PoseUtils.get_landmark(landmarks, rs["RIGHT_KNEE"])

        # Detect dominant side by wrist visibility/x position
        dominant = "right" if right_wrist.get("visibility", 0) >= left_wrist.get("visibility", 0) else "left"

        # Serve practice checks
        if "Serve" in skill_name or skill_name.lower().startswith("serve"):
            # Toss alignment: nose roughly above front foot / between shoulders
            mid_shoulder_x = (left_shoulder["x"] + right_shoulder["x"]) / 2
            if abs(nose["x"] - mid_shoulder_x) < 0.07:
                feedback.append("✅ Good toss alignment under control.")
            else:
                feedback.append("⚠️ Toss alignment off - try to toss vertically in front of your body.")
                technique_score -= 10.0

            # Racket ready position: elbow up and wrist near shoulder height
            shoulder = right_shoulder if dominant == "right" else left_shoulder
            elbow = right_elbow if dominant == "right" else left_elbow
            wrist = right_wrist if dominant == "right" else left_wrist
            elb_angle = PoseUtils.calculate_angle(shoulder, elbow, wrist)
            if 70 <= elb_angle <= 120:
                feedback.append("✅ Ready racket position for serve.")
            else:
                feedback.append("⚠️ Adjust racket preparation - elbow angle should be ~90°.")
                technique_score -= 8.0

        # Forehand/backhand stroke checks
        if "Forehand" in skill_name or "Backhand" in skill_name:
            shoulder = right_shoulder if dominant == "right" else left_shoulder
            elbow = right_elbow if dominant == "right" else left_elbow
            wrist = right_wrist if dominant == "right" else left_wrist
            arm_angle = PoseUtils.calculate_angle(shoulder, elbow, wrist)
            if arm_angle >= 135:
                feedback.append("✅ Good arm extension through contact.")
            elif arm_angle >= 110:
                feedback.append("⚠️ Slightly limited extension - follow through more.")
                technique_score -= 6.0
            else:
                feedback.append("❌ Limited extension - extend arm more for power.")
                technique_score -= 15.0

        # Footwork & weight transfer hints
        hip_diff = abs(left_hip["x"] - right_hip["x"])
        knee_diff = abs(left_knee["y"] - right_knee["y"])
        if hip_diff > 0.12:
            feedback.append("✅ Good weight shift across hips.")
        else:
            feedback.append("⚠️ Increase weight transfer for more power.")
            technique_score -= 6.0

        if knee_diff > 0.06:
            feedback.append("⚠️ Uneven knee heights - check landing and balance.")
            technique_score -= 4.0

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        overall_score = max(0.0, technique_score * 0.65 + balance_score * 0.35)

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
        return ["Forehand", "Backhand", "Serve", "Volley", "Footwork Drill"]
