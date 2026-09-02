from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.mirroring import get_dominant_and_off_side
from ..shared.skill_profiles import effective_min, scale_penalty
from ..shared.utils import PoseUtils


class TennisAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(sport_type="tennis")

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        rs = PoseUtils.LANDMARKS
        nose = PoseUtils.get_landmark(landmarks, rs["NOSE"])
        left_shoulder = PoseUtils.get_landmark(landmarks, rs["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, rs["RIGHT_SHOULDER"])

        # Racket arm resolved from Athlete.dominant_hand instead of a
        # per-frame visibility guess (which could flip side frame-to-frame).
        dom, _off, _side = get_dominant_and_off_side(landmarks, dominant_hand)

        # Serve practice checks
        if "Serve" in skill_name or skill_name.lower().startswith("serve"):
            if PoseUtils.is_confident(nose) and PoseUtils.is_confident(left_shoulder) and PoseUtils.is_confident(right_shoulder):
                mid_shoulder_x = (left_shoulder["x"] + right_shoulder["x"]) / 2
                delta, msg = self.check_max(
                    abs(nose["x"] - mid_shoulder_x), 0.07, skill_level, penalty=10,
                    pass_msg="✅ Good toss alignment under control.",
                    fail_msg="⚠️ Toss alignment off - try to toss vertically in front of your body.",
                )
                technique_score += delta
                feedback.append(msg)

            elb_angle = PoseUtils.calculate_angle_safe(dom.shoulder, dom.elbow, dom.wrist)
            delta, msg = self.check_range(
                elb_angle, 70, 120, skill_level, penalty=8,
                pass_msg="✅ Ready racket position for serve.",
                low_msg="⚠️ Adjust racket preparation - elbow angle should be ~90°.",
                high_msg="⚠️ Adjust racket preparation - elbow angle should be ~90°.",
            )
            technique_score += delta
            if msg:
                feedback.append(msg)

        # Forehand/backhand stroke checks
        if "Forehand" in skill_name or "Backhand" in skill_name:
            arm_angle = PoseUtils.calculate_angle_safe(dom.shoulder, dom.elbow, dom.wrist)
            if arm_angle is not None:
                good_threshold = effective_min(135, skill_level)
                ok_threshold = effective_min(110, skill_level)
                if arm_angle >= good_threshold:
                    feedback.append("✅ Good arm extension through contact.")
                elif arm_angle >= ok_threshold:
                    feedback.append("⚠️ Slightly limited extension - follow through more.")
                    technique_score -= scale_penalty(6.0, skill_level)
                else:
                    feedback.append("❌ Limited extension - extend arm more for power.")
                    technique_score -= scale_penalty(15.0, skill_level)

        # Footwork & weight transfer hints
        if PoseUtils.is_confident(dom.hip) and PoseUtils.is_confident(_off.hip):
            hip_diff = abs(dom.hip["x"] - _off.hip["x"])
            delta, msg = self.check_min(
                hip_diff, 0.12, skill_level, penalty=6,
                pass_msg="✅ Good weight shift across hips.",
                fail_msg="⚠️ Increase weight transfer for more power.",
            )
            technique_score += delta
            feedback.append(msg)

        if PoseUtils.is_confident(dom.knee) and PoseUtils.is_confident(_off.knee):
            knee_diff = abs(dom.knee["y"] - _off.knee["y"])
            if knee_diff > 0.06:
                feedback.append("⚠️ Uneven knee heights - check landing and balance.")
                technique_score -= scale_penalty(4.0, skill_level)

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        technique_score = max(0.0, technique_score)
        overall_score = self.blend_scores(technique_score, balance_score, 0.65)

        return {
            "score": overall_score,
            "technique_accuracy": technique_score,
            "balance_score": balance_score,
            "feedback": feedback,
        }

    def get_supported_skills(self) -> List[str]:
        return ["Forehand", "Backhand", "Serve", "Volley", "Footwork Drill"]
