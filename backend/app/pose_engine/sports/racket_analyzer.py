from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.mirroring import get_dominant_and_off_side
from ..shared.skill_profiles import effective_min, scale_penalty
from ..shared.utils import PoseUtils


class RacketAnalyzer(BaseAnalyzer):
    def __init__(self, sport_type: str = "racket"):
        super().__init__(sport_type=sport_type)

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        # Generic racket checks: arm extension, wrist position, knee bend -
        # resolved to the athlete's dominant/racket side.
        dom, _off, _side = get_dominant_and_off_side(landmarks, dominant_hand)

        arm_angle = PoseUtils.calculate_angle_safe(dom.shoulder, dom.elbow, dom.wrist)
        if arm_angle is not None:
            good_threshold = effective_min(140, skill_level)
            ok_threshold = effective_min(120, skill_level)
            if arm_angle >= good_threshold:
                feedback.append("✅ Good arm extension for racket strike.")
            elif arm_angle >= ok_threshold:
                feedback.append("⚠️ Slightly bent arm - extend more for power.")
                technique_score -= scale_penalty(8.0, skill_level)
            else:
                feedback.append("❌ Arm too bent - extend through contact.")
                technique_score -= scale_penalty(18.0, skill_level)

        knee_angle = PoseUtils.calculate_angle_safe(dom.hip, dom.knee, dom.ankle)
        delta, msg = self.check_range(
            knee_angle, 130, 170, skill_level, penalty=6,
            pass_msg="✅ Stable knee bend for racket movement.",
            low_msg="⚠️ Adjust knee bend for stability and mobility.",
            high_msg="⚠️ Adjust knee bend for stability and mobility.",
        )
        technique_score += delta
        if msg:
            feedback.append(msg)

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        technique_score = max(0.0, technique_score)
        overall_score = self.blend_scores(technique_score, balance_score, 0.7)

        return {
            "score": overall_score,
            "technique_accuracy": technique_score,
            "balance_score": balance_score,
            "feedback": feedback,
        }

    def get_supported_skills(self) -> List[str]:
        return ["Forehand", "Backhand", "Serve", "Volley", "Smash"]
