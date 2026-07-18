from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class BoxingAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="boxing")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        feedback = []
        joint_angles = {}
        technique_score = 100.0

        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        left_elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_ELBOW"])
        right_elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ELBOW"])
        left_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_WRIST"])
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        left_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_HIP"])
        right_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_HIP"])

        if "Guard" in skill_name or skill_name == "Guard Position":
            avg_shoulder_y = (left_shoulder["y"] + right_shoulder["y"]) / 2
            if left_wrist["y"] < avg_shoulder_y and right_wrist["y"] < avg_shoulder_y:
                feedback.append("✅ Good guard position - hands up.")
            else:
                feedback.append("❌ Guard dropped - keep hands up at chin level.")
                technique_score -= 20.0

            left_elbow_angle = PoseUtils.calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = PoseUtils.calculate_angle(right_shoulder, right_elbow, right_wrist)
            joint_angles["left_elbow"] = left_elbow_angle
            joint_angles["right_elbow"] = right_elbow_angle
            if 60 <= left_elbow_angle <= 110 and 60 <= right_elbow_angle <= 110:
                feedback.append("✅ Elbows properly tucked.")
            else:
                feedback.append("⚠️ Tuck elbows closer to body.")
                technique_score -= 10.0

        if skill_name in ["Jab", "Cross"]:
            if skill_name == "Jab":
                punch_shoulder = left_shoulder
                punch_elbow = left_elbow
                punch_wrist = left_wrist
                guard_wrist = right_wrist
                punch_side = "left"
            else:
                punch_shoulder = right_shoulder
                punch_elbow = right_elbow
                punch_wrist = right_wrist
                guard_wrist = left_wrist
                punch_side = "right"

            punch_angle = PoseUtils.calculate_angle(punch_shoulder, punch_elbow, punch_wrist)
            joint_angles["punch_extension"] = punch_angle
            if punch_angle > 160:
                feedback.append("✅ Full punch extension.")
            elif punch_angle > 140:
                feedback.append("⚠️ Punch not fully extended.")
                technique_score -= 10.0
            else:
                feedback.append("❌ Punch too short - extend fully.")
                technique_score -= 20.0

            if guard_wrist["y"] < punch_shoulder["y"]:
                feedback.append("✅ Guard hand maintained.")
            else:
                feedback.append("❌ Guard hand dropped - protect your face.")
                technique_score -= 15.0

            if skill_name == "Cross":
                hip_rotation = abs(left_hip["x"] - right_hip["x"])
                if hip_rotation > 0.1:
                    feedback.append("✅ Good hip rotation.")
                else:
                    feedback.append("⚠️ Rotate hips more for power.")
                    technique_score -= 10.0

        if "Hook" in skill_name:
            left_elbow_angle = PoseUtils.calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = PoseUtils.calculate_angle(right_shoulder, right_elbow, right_wrist)
            hook_angle = left_elbow_angle if left_wrist["x"] < right_wrist["x"] else right_elbow_angle
            joint_angles["hook_elbow"] = hook_angle
            if 80 <= hook_angle <= 100:
                feedback.append("✅ Perfect 90-degree elbow for hook.")
            else:
                feedback.append("❌ Maintain 90-degree elbow bend for hook.")
                technique_score -= 15.0

        if "Uppercut" in skill_name:
            if left_wrist["y"] < left_shoulder["y"] or right_wrist["y"] < right_shoulder["y"]:
                feedback.append("✅ Good upward drive.")
            else:
                feedback.append("⚠️ Drive upward more with legs.")
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

        # Detect punch combinations across frames: look for punch_extension > threshold
        punch_values = [r.get("joint_angles", {}).get("punch_extension") for r in frame_results]
        combos = 0
        current_combo = 0
        for v in punch_values:
            if v is None:
                current_combo = 0
                continue
            if v > 140:
                current_combo += 1
            else:
                if current_combo >= 2:
                    combos += 1
                current_combo = 0
        if current_combo >= 2:
            combos += 1

        return {
            "overall_score": round(avg_score, 2),
            "technique_accuracy": round(avg_tech, 2),
            "balance_score": round(avg_balance, 2),
            "frame_count": len(frame_results),
            "detailed": {"combination_count": combos},
        }

    def get_supported_skills(self) -> List[str]:
        return [
            "Jab",
            "Cross",
            "Hook",
            "Uppercut",
            "Guard Position",
            "Slip & Roll",
            "Pivot Footwork",
            "Combination Drills",
        ]
