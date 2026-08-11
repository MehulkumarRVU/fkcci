from typing import Any, Dict, List, Optional
from ..base_analyzer import BaseAnalyzer
from ..shared.utils import PoseUtils


class AIGymCoachAnalyzer(BaseAnalyzer):
    def __init__(self, sport_type: str = "ai_gym_coach"):
        super().__init__(sport_type=sport_type)

    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str,
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict[str, Any]:
        feedback = []
        technique_score = 100.0
        joint_angles = {}

        left_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_HIP"])
        left_knee = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_KNEE"])
        left_ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_ANKLE"])
        left_shoulder = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
        left_elbow = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_ELBOW"])
        left_wrist = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_WRIST"])

        skill_lower = skill_name.lower()

        if "squat" in skill_lower:
            knee_angle = PoseUtils.calculate_angle_safe(left_hip, left_knee, left_ankle)
            if knee_angle is not None:
                joint_angles["knee_flexion"] = knee_angle
            delta, msg = self.check_max(
                knee_angle, 140, skill_level, penalty=8,
                pass_msg="✅ Deep squat — good range of motion.",
                fail_msg="⚠️ Not deep enough — lower hips to improve range.",
            )
            technique_score += delta
            if msg:
                feedback.append(msg)

        elif "push-up" in skill_lower or "push up" in skill_lower or "pushup" in skill_lower:
            # Elbow flexion at the bottom of a push-up, and a straight-body
            # (no sagging hips) check - previously push-ups fell through to
            # no sport-specific logic at all despite being an offered skill.
            elbow_angle = PoseUtils.calculate_angle_safe(left_shoulder, left_elbow, left_wrist)
            if elbow_angle is not None:
                joint_angles["elbow_flexion"] = elbow_angle
            delta, msg = self.check_max(
                elbow_angle, 100, skill_level, penalty=8,
                pass_msg="✅ Good depth — chest low on the down phase.",
                fail_msg="⚠️ Lower further for full range of motion.",
            )
            technique_score += delta
            if msg:
                feedback.append(msg)

            body_line = PoseUtils.calculate_angle_safe(left_shoulder, left_hip, left_knee)
            if body_line is not None:
                joint_angles["body_line"] = body_line
            delta, msg = self.check_min(
                body_line, 160, skill_level, penalty=10,
                pass_msg="✅ Straight body line - good core engagement.",
                fail_msg="⚠️ Hips sagging or piking - keep your core tight.",
            )
            technique_score += delta
            if msg:
                feedback.append(msg)

        balance_score, balance_feedback = PoseUtils.analyze_balance(landmarks)
        feedback.append(balance_feedback)

        technique_score = max(0.0, technique_score)
        return {
            "score": self.blend_scores(technique_score, balance_score, 0.6),
            "technique_accuracy": technique_score,
            "balance_score": balance_score,
            "feedback": feedback,
            "joint_angles": joint_angles,
        }

    def analyze_session(self, pose_sequence: List[List[Dict[str, float]]], skill_name: str,
                         skill_level: str = "beginner", dominant_hand: str = "right",
                         timestamps: Optional[List[float]] = None) -> Dict[str, Any]:
        result = super().analyze_session(pose_sequence, skill_name, skill_level, dominant_hand, timestamps)

        skill_lower = skill_name.lower()
        angles = []
        for frame in pose_sequence:
            if "push-up" in skill_lower or "push up" in skill_lower or "pushup" in skill_lower:
                s = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_SHOULDER"])
                e = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_ELBOW"])
                w = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_WRIST"])
                angles.append(PoseUtils.calculate_angle(s, e, w))
            else:
                h = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_HIP"])
                k = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_KNEE"])
                a = PoseUtils.get_landmark(frame, PoseUtils.LANDMARKS["LEFT_ANKLE"])
                angles.append(PoseUtils.calculate_angle(h, k, a))

        down_threshold, up_threshold = (100, 150) if ("push" in skill_lower) else (140, 160)
        reps = 0
        in_down = False
        for a in angles:
            if a < down_threshold and not in_down:
                in_down = True
            if a >= up_threshold and in_down:
                reps += 1
                in_down = False

        result["detailed"] = {"estimated_reps": reps}
        return result

    def get_supported_skills(self) -> List[str]:
        return ["Squat Form", "Push-Up Form", "Rep Counting"]
