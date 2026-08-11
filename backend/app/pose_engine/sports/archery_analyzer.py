from typing import Any, Dict, List
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class ArcheryAnalyzer(BaseAnalyzer):
    def __init__(self, sport_type: str = "indoor_archery"):
        super().__init__(sport_type=sport_type)

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0

        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_SHOULDER"])
        nose = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["NOSE"])
        left_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_WRIST"])
        right_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_WRIST"])

        # Alignment check: nose should be near shoulder midline when aiming
        alignment_offset = None
        if PoseUtils.is_confident(left_shoulder) and PoseUtils.is_confident(right_shoulder) and PoseUtils.is_confident(nose):
            mid_shoulder_x = (left_shoulder["x"] + right_shoulder["x"]) / 2
            alignment_offset = abs(nose["x"] - mid_shoulder_x)
        delta, msg = self.check_max(
            alignment_offset, 0.06, skill_level, penalty=8,
            pass_msg="✅ Good head alignment with shoulders.",
            fail_msg="⚠️ Head alignment off - square shoulders to target.",
        )
        technique_score += delta
        if msg:
            feedback.append(msg)

        # Draw-arm separation: bow arm should stay extended while draw hand
        # is pulled back toward the face (distinguishes the three archery
        # skills instead of applying identical logic to all of them).
        if PoseUtils.is_confident(left_wrist) and PoseUtils.is_confident(right_wrist) and PoseUtils.is_confident(nose):
            draw_hand_to_face = min(
                PoseUtils.calculate_distance(left_wrist, nose),
                PoseUtils.calculate_distance(right_wrist, nose),
            )
            if "Draw" in skill_name or "Anchor" in skill_name:
                delta2, msg2 = self.check_max(
                    draw_hand_to_face, 0.15, skill_level, penalty=8,
                    pass_msg="✅ Solid anchor point near the face.",
                    fail_msg="⚠️ Bring your draw hand closer to a consistent anchor point.",
                )
                technique_score += delta2
                feedback.append(msg2)
            elif "Release" in skill_name:
                delta2, msg2 = self.check_min(
                    draw_hand_to_face, 0.02, skill_level, penalty=6,
                    pass_msg="✅ Clean release follow-through.",
                    fail_msg="⚠️ Follow through more after release.",
                )
                technique_score += delta2
                feedback.append(msg2)

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
        return ["Draw & Anchor", "Aim Stability", "Release"]
