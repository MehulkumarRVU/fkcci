from typing import Any, Dict, List, Optional
from ..base_analyzer import BaseAnalyzer
from ..shared.confidence import DEFAULT_GATE
from ..shared.mirroring import boxing_stance_sides
from ..shared.reference_compare import classify_deviation
from ..shared.scoring import combine_scores
from ..shared.skill_profiles import effective_min, scale_penalty
from ..shared.utils import PoseUtils


def _side_landmarks(landmarks, side):
    L = PoseUtils.LANDMARKS
    prefix = "LEFT" if side == "left" else "RIGHT"
    return (
        PoseUtils.get_landmark(landmarks, L[f"{prefix}_SHOULDER"]),
        PoseUtils.get_landmark(landmarks, L[f"{prefix}_ELBOW"]),
        PoseUtils.get_landmark(landmarks, L[f"{prefix}_WRIST"]),
    )


class BoxingAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="boxing")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        joint_angles = {}
        deviations = {}
        technique_score = 100.0

        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        left_elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_ELBOW"])
        right_elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ELBOW"])
        left_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_WRIST"])
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])
        left_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_HIP"])
        right_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_HIP"])

        # Orthodox (right-handed) leads with the left hand and powers with
        # the right; southpaw (left-handed) is mirrored. Previously this
        # analyzer hardcoded Jab=left/Cross=right regardless of stance, so a
        # southpaw's jab/cross were scored on the wrong arm entirely.
        lead_side, power_side = boxing_stance_sides(dominant_hand)

        if "Guard" in skill_name or skill_name == "Guard Position":
            if PoseUtils.is_confident(left_shoulder) and PoseUtils.is_confident(right_shoulder) \
                    and PoseUtils.is_confident(left_wrist) and PoseUtils.is_confident(right_wrist):
                avg_shoulder_y = (left_shoulder["y"] + right_shoulder["y"]) / 2
                if left_wrist["y"] < avg_shoulder_y and right_wrist["y"] < avg_shoulder_y:
                    feedback.append("✅ Good guard position - hands up.")
                else:
                    feedback.append("❌ Guard dropped - keep hands up at chin level.")
                    technique_score -= scale_penalty(20.0, skill_level)

            left_elbow_angle = PoseUtils.calculate_angle_safe(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = PoseUtils.calculate_angle_safe(right_shoulder, right_elbow, right_wrist)
            if left_elbow_angle is not None:
                joint_angles["left_elbow"] = left_elbow_angle
            if right_elbow_angle is not None:
                joint_angles["right_elbow"] = right_elbow_angle
            if left_elbow_angle is not None and right_elbow_angle is not None:
                delta_l, _ = self.check_range(left_elbow_angle, 60, 110, skill_level, penalty=10,
                                               pass_msg=None, low_msg=None, high_msg=None)
                delta_r, _ = self.check_range(right_elbow_angle, 60, 110, skill_level, penalty=10,
                                               pass_msg=None, low_msg=None, high_msg=None)
                if delta_l == 0.0 and delta_r == 0.0:
                    feedback.append("✅ Elbows properly tucked.")
                else:
                    feedback.append("⚠️ Tuck elbows closer to body.")
                    technique_score -= scale_penalty(10.0, skill_level)

        if skill_name in ["Jab", "Cross"]:
            punch_side = lead_side if skill_name == "Jab" else power_side
            guard_side = power_side if skill_name == "Jab" else lead_side
            punch_shoulder, punch_elbow, punch_wrist = _side_landmarks(landmarks, punch_side)
            _, _, guard_wrist = _side_landmarks(landmarks, guard_side)

            punch_angle = PoseUtils.calculate_angle_safe(punch_shoulder, punch_elbow, punch_wrist)
            if punch_angle is not None:
                joint_angles["punch_extension"] = punch_angle
            if punch_angle is not None:
                full_threshold = effective_min(160, skill_level)
                partial_threshold = effective_min(140, skill_level)
                if punch_angle > full_threshold:
                    feedback.append("✅ Full punch extension.")
                elif punch_angle > partial_threshold:
                    feedback.append("⚠️ Punch not fully extended.")
                    technique_score -= scale_penalty(10.0, skill_level)
                else:
                    feedback.append("❌ Punch too short - extend fully.")
                    technique_score -= scale_penalty(20.0, skill_level)
                severity = classify_deviation(punch_angle, full_threshold, 180)
                if severity:
                    punch_elbow_index = PoseUtils.LANDMARKS[f"{'LEFT' if punch_side == 'left' else 'RIGHT'}_ELBOW"]
                    deviations[punch_elbow_index] = severity

            if PoseUtils.is_confident(guard_wrist) and PoseUtils.is_confident(punch_shoulder):
                if guard_wrist["y"] < punch_shoulder["y"]:
                    feedback.append("✅ Guard hand maintained.")
                else:
                    feedback.append("❌ Guard hand dropped - protect your face.")
                    technique_score -= scale_penalty(15.0, skill_level)

            if skill_name == "Cross" and PoseUtils.is_confident(left_hip) and PoseUtils.is_confident(right_hip):
                hip_rotation = abs(left_hip["x"] - right_hip["x"])
                delta, msg = self.check_min(
                    hip_rotation, 0.1, skill_level, penalty=10,
                    pass_msg="✅ Good hip rotation.",
                    fail_msg="⚠️ Rotate hips more for power.",
                )
                technique_score += delta
                feedback.append(msg)

        if "Hook" in skill_name:
            left_elbow_angle = PoseUtils.calculate_angle_safe(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = PoseUtils.calculate_angle_safe(right_shoulder, right_elbow, right_wrist)
            hook_angle = None
            if left_elbow_angle is not None and right_elbow_angle is not None and PoseUtils.is_confident(left_wrist) and PoseUtils.is_confident(right_wrist):
                hook_angle = left_elbow_angle if left_wrist["x"] < right_wrist["x"] else right_elbow_angle
            if hook_angle is not None:
                joint_angles["hook_elbow"] = hook_angle
            delta, msg = self.check_range(
                hook_angle, 80, 100, skill_level, penalty=15,
                pass_msg="✅ Perfect 90-degree elbow for hook.",
                low_msg="❌ Maintain 90-degree elbow bend for hook.",
                high_msg="❌ Maintain 90-degree elbow bend for hook.",
            )
            technique_score += delta
            if msg:
                feedback.append(msg)
            severity = classify_deviation(hook_angle, 80, 100)
            if severity and hook_angle is not None:
                hook_side = "left" if (PoseUtils.is_confident(left_wrist) and PoseUtils.is_confident(right_wrist) and left_wrist["x"] < right_wrist["x"]) else "right"
                deviations[PoseUtils.LANDMARKS[f"{'LEFT' if hook_side == 'left' else 'RIGHT'}_ELBOW"]] = severity

        if "Uppercut" in skill_name and PoseUtils.is_confident(left_wrist) and PoseUtils.is_confident(left_shoulder) \
                and PoseUtils.is_confident(right_wrist) and PoseUtils.is_confident(right_shoulder):
            if left_wrist["y"] < left_shoulder["y"] or right_wrist["y"] < right_shoulder["y"]:
                feedback.append("✅ Good upward drive.")
            else:
                feedback.append("⚠️ Drive upward more with legs.")
                technique_score -= scale_penalty(10.0, skill_level)

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        breakdown = combine_scores(
            technique_score=technique_score,
            balance_score=balance_score,
            technique_weight=0.7,
            pose_confidence=DEFAULT_GATE.coverage(landmarks),
            feedback=feedback,
            joint_angles=joint_angles,
        )
        result = breakdown.as_dict()
        result["stance"] = "southpaw" if lead_side == "right" else "orthodox"
        result["deviations"] = deviations
        return result

    def analyze_session(self, pose_sequence: List[List[Dict[str, float]]], skill_name: str,
                         skill_level: str = "beginner", dominant_hand: str = "right",
                         timestamps: Optional[List[float]] = None) -> Dict[str, Any]:
        result = super().analyze_session(pose_sequence, skill_name, skill_level, dominant_hand, timestamps)

        # Detect punch combinations across frames: consecutive frames with
        # punch_extension > 140 degrees.
        frame_results = [self.analyze_frame(frame, skill_name, skill_level, dominant_hand) for frame in pose_sequence]
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

        result["detailed"] = {"combination_count": combos}
        return result

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
