import math
from typing import Dict, List, Tuple


class PoseUtils:
    LANDMARKS = {
        "NOSE": 0,
        "LEFT_EYE": 2,
        "RIGHT_EYE": 5,
        "LEFT_EAR": 7,
        "RIGHT_EAR": 8,
        "LEFT_SHOULDER": 11,
        "RIGHT_SHOULDER": 12,
        "LEFT_ELBOW": 13,
        "RIGHT_ELBOW": 14,
        "LEFT_WRIST": 15,
        "RIGHT_WRIST": 16,
        "LEFT_HIP": 23,
        "RIGHT_HIP": 24,
        "LEFT_KNEE": 25,
        "RIGHT_KNEE": 26,
        "LEFT_ANKLE": 27,
        "RIGHT_ANKLE": 28,
    }

    @staticmethod
    def get_landmark(landmarks: List[Dict[str, float]], index: int) -> Dict[str, float]:
        if index < len(landmarks):
            return landmarks[index]
        return {"x": 0.0, "y": 0.0, "z": 0.0, "visibility": 0.0}

    @staticmethod
    def calculate_angle(a: Dict[str, float], b: Dict[str, float], c: Dict[str, float]) -> float:
        try:
            ba_x = a["x"] - b["x"]
            ba_y = a["y"] - b["y"]
            bc_x = c["x"] - b["x"]
            bc_y = c["y"] - b["y"]

            dot_product = ba_x * bc_x + ba_y * bc_y
            magnitude_ba = math.sqrt(ba_x**2 + ba_y**2)
            magnitude_bc = math.sqrt(bc_x**2 + bc_y**2)

            if magnitude_ba == 0 or magnitude_bc == 0:
                return 0.0

            cos_angle = dot_product / (magnitude_ba * magnitude_bc)
            cos_angle = max(-1.0, min(1.0, cos_angle))
            return math.degrees(math.acos(cos_angle))
        except Exception:
            return 0.0

    @staticmethod
    def calculate_distance(a: Dict[str, float], b: Dict[str, float]) -> float:
        return math.sqrt((a["x"] - b["x"])**2 + (a["y"] - b["y"])**2)

    @staticmethod
    def analyze_balance(landmarks: List[Dict[str, float]]) -> Tuple[float, str]:
        left_ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_ANKLE"])
        right_ankle = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_ANKLE"])
        left_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["LEFT_HIP"])
        right_hip = PoseUtils.get_landmark(landmarks, PoseUtils.LANDMARKS["RIGHT_HIP"])

        ankle_width = abs(left_ankle["x"] - right_ankle["x"])
        hip_width = abs(left_hip["x"] - right_hip["x"])

        balance_score = 100.0
        feedback = "Good balance and stance width."

        if hip_width > 0 and ankle_width < hip_width * 0.8:
            balance_score = 70.0
            feedback = "⚠️ Stance too narrow - widen your feet."
        elif hip_width > 0 and ankle_width > hip_width * 2:
            balance_score = 75.0
            feedback = "⚠️ Stance too wide - bring feet closer together."

        ankle_level_diff = abs(left_ankle["y"] - right_ankle["y"])
        if ankle_level_diff > 0.05:
            balance_score = max(0.0, balance_score - 10.0)
            feedback += " Uneven weight distribution."

        return balance_score, feedback
