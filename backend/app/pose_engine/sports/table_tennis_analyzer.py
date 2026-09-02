from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.confidence import DEFAULT_GATE
from ..shared.mirroring import get_dominant_and_off_side
from ..shared.reference_compare import classify_deviation
from ..shared.scoring import combine_scores
from ..shared.skill_profiles import scale_penalty
from ..shared.utils import PoseUtils


class TableTennisAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="table_tennis")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        joint_angles = {}
        technique_score = 100.0

        # Resolves to the athlete's actual playing arm instead of always
        # reading the right side - a left-handed athlete's technique was
        # previously scored using their non-dominant arm.
        dom, _off, side = get_dominant_and_off_side(landmarks, dominant_hand)
        L = PoseUtils.LANDMARKS
        prefix = "LEFT" if side == "left" else "RIGHT"
        deviations = {}

        arm_angle = PoseUtils.calculate_angle_safe(dom.shoulder, dom.elbow, dom.wrist)
        if arm_angle is not None:
            joint_angles["arm_extension"] = arm_angle
        if "Drive" in skill_name or "Topspin" in skill_name:
            delta, msg = self.check_range(
                arm_angle, 130, 170, skill_level, penalty=10,
                pass_msg="✅ Good arm extension.",
                low_msg="❌ Elbow too bent - extend more.",
                high_msg="⚠️ Arm too straight - slight bend needed.",
                low_penalty=15, high_penalty=10,
            )
            technique_score += delta
            if msg:
                feedback.append(msg)
            severity = classify_deviation(arm_angle, 130, 170)
            if severity:
                deviations[L[f"{prefix}_ELBOW"]] = severity

        knee_angle = PoseUtils.calculate_angle_safe(dom.hip, dom.knee, dom.ankle)
        if knee_angle is not None:
            joint_angles["knee_flexion"] = knee_angle
        delta, msg = self.check_range(
            knee_angle, 140, 170, skill_level, penalty=10,
            pass_msg="✅ Good knee bend for stability.",
            low_msg="⚠️ Too much knee bend - raise up slightly.",
            high_msg="❌ Insufficient knee bend - lower your stance.",
            low_penalty=10, high_penalty=15,
        )
        technique_score += delta
        if msg:
            feedback.append(msg)
        severity = classify_deviation(knee_angle, 140, 170)
        if severity:
            deviations[L[f"{prefix}_KNEE"]] = severity

        if PoseUtils.is_confident(dom.elbow) and PoseUtils.is_confident(dom.shoulder):
            if dom.elbow["y"] > dom.shoulder["y"] + 0.1:
                feedback.append("❌ Elbow too low - keep it up.")
                technique_score -= scale_penalty(15.0, skill_level)

        if "Topspin" in skill_name and PoseUtils.is_confident(dom.wrist) and PoseUtils.is_confident(dom.elbow):
            if dom.wrist["y"] < dom.elbow["y"]:
                feedback.append("✅ Good wrist position for topspin.")
            else:
                feedback.append("⚠️ Wrist should be higher than elbow for topspin.")
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
        result["dominant_side_used"] = side
        result["deviations"] = deviations
        return result

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
