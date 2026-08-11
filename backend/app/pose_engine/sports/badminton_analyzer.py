from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.mirroring import get_dominant_and_off_side
from ..shared.skill_profiles import effective_min, scale_penalty
from ..shared.utils import PoseUtils


class BadmintonAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="badminton")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        joint_angles = {}
        technique_score = 100.0

        # Racket arm resolved from the athlete's dominant hand instead of
        # always reading the right side.
        dom, off, _side = get_dominant_and_off_side(landmarks, dominant_hand)

        if "Serve" in skill_name or "Clear" in skill_name or "Smash" in skill_name:
            arm_angle = PoseUtils.calculate_angle_safe(dom.shoulder, dom.elbow, dom.wrist)
            if arm_angle is not None:
                joint_angles["arm_extension"] = arm_angle
            if arm_angle is not None:
                strong_threshold = effective_min(150, skill_level)
                ok_threshold = effective_min(130, skill_level)
                if arm_angle >= strong_threshold:
                    feedback.append("✅ Strong extension and reach.")
                elif arm_angle >= ok_threshold:
                    feedback.append("⚠️ Good extension, keep the arm straighter for more power.")
                    technique_score -= scale_penalty(10.0, skill_level)
                else:
                    feedback.append("❌ Arm too bent - extend more through the shot.")
                    technique_score -= scale_penalty(20.0, skill_level)

        if "Footwork" in skill_name or "Movement" in skill_name:
            # Footwork/split-step is assessed on the non-racket (support) leg.
            knee_angle = PoseUtils.calculate_angle_safe(off.hip, off.knee, off.ankle)
            if knee_angle is not None:
                joint_angles["knee_bend"] = knee_angle
            delta, msg = self.check_range(
                knee_angle, 140, 170, skill_level, penalty=10,
                pass_msg="✅ Good knee bend for quick badminton footwork.",
                low_msg="⚠️ Slightly bend your knees more for better balance.",
                high_msg="⚠️ Avoid over-bending and losing mobility.",
                low_penalty=10, high_penalty=5,
            )
            technique_score += delta
            if msg:
                feedback.append(msg)

        if "Net Play" in skill_name and PoseUtils.is_confident(dom.wrist) and PoseUtils.is_confident(dom.elbow):
            if dom.wrist["y"] < dom.elbow["y"]:
                feedback.append("✅ Good wrist position for net control.")
            else:
                feedback.append("⚠️ Keep your racket hand higher for delicate net shots.")
                technique_score -= scale_penalty(10.0, skill_level)

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        technique_score = max(0.0, technique_score)
        overall_score = self.blend_scores(technique_score, balance_score, 0.65)

        return {
            "score": overall_score,
            "technique_accuracy": technique_score,
            "balance_score": balance_score,
            "feedback": feedback,
            "joint_angles": joint_angles,
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
