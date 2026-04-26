import math
from typing import List, Dict, Tuple


class SportsPoseAnalyzer:
    """Analyzes pose landmarks for Table Tennis and Boxing techniques"""
    
    # MediaPipe Pose Landmark indices
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
    
    def __init__(self, sport_type: str):
        self.sport_type = sport_type
    
    def calculate_angle(self, a: Dict, b: Dict, c: Dict) -> float:
        """Calculate angle between three points (a-b-c)"""
        try:
            # Vector BA
            ba_x = a['x'] - b['x']
            ba_y = a['y'] - b['y']
            
            # Vector BC
            bc_x = c['x'] - b['x']
            bc_y = c['y'] - b['y']
            
            # Dot product
            dot_product = ba_x * bc_x + ba_y * bc_y
            
            # Magnitudes
            magnitude_ba = math.sqrt(ba_x**2 + ba_y**2)
            magnitude_bc = math.sqrt(bc_x**2 + bc_y**2)
            
            # Avoid division by zero
            if magnitude_ba == 0 or magnitude_bc == 0:
                return 0
            
            # Calculate angle
            cos_angle = dot_product / (magnitude_ba * magnitude_bc)
            cos_angle = max(-1, min(1, cos_angle))  # Clamp to [-1, 1]
            
            angle = math.acos(cos_angle)
            return math.degrees(angle)
        except:
            return 0
    
    def calculate_distance(self, a: Dict, b: Dict) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2)
    
    def get_landmark(self, landmarks: List[Dict], index: int) -> Dict:
        """Get landmark by index"""
        if index < len(landmarks):
            return landmarks[index]
        return {"x": 0, "y": 0, "z": 0, "visibility": 0}
    
    def analyze_balance(self, landmarks: List[Dict]) -> Tuple[float, str]:
        """Analyze balance and stability"""
        left_ankle = self.get_landmark(landmarks, self.LANDMARKS["LEFT_ANKLE"])
        right_ankle = self.get_landmark(landmarks, self.LANDMARKS["RIGHT_ANKLE"])
        left_hip = self.get_landmark(landmarks, self.LANDMARKS["LEFT_HIP"])
        right_hip = self.get_landmark(landmarks, self.LANDMARKS["RIGHT_HIP"])
        
        # Check stance width
        ankle_width = abs(left_ankle['x'] - right_ankle['x'])
        hip_width = abs(left_hip['x'] - right_hip['x'])
        
        # Good balance: ankles slightly wider than hips
        balance_score = 100
        feedback = "Good balance and stance width."
        
        if ankle_width < hip_width * 0.8:
            balance_score = 70
            feedback = "⚠️ Stance too narrow - widen your feet."
        elif ankle_width > hip_width * 2:
            balance_score = 75
            feedback = "⚠️ Stance too wide - bring feet closer together."
        
        # Check for weight distribution (check if ankles are level)
        ankle_level_diff = abs(left_ankle['y'] - right_ankle['y'])
        if ankle_level_diff > 0.05:
            balance_score -= 10
            feedback += " Uneven weight distribution."
        
        return balance_score, feedback
    
    def analyze_table_tennis(self, landmarks: List[Dict], skill_name: str) -> Dict:
        """Analyze Table Tennis specific techniques"""
        feedback = []
        joint_angles = {}
        technique_score = 100
        
        dominant_side = "RIGHT"  # Assume right-handed for now
        
        if dominant_side == "RIGHT":
            shoulder_idx = self.LANDMARKS["RIGHT_SHOULDER"]
            elbow_idx = self.LANDMARKS["RIGHT_ELBOW"]
            wrist_idx = self.LANDMARKS["RIGHT_WRIST"]
            hip_idx = self.LANDMARKS["RIGHT_HIP"]
            knee_idx = self.LANDMARKS["RIGHT_KNEE"]
            ankle_idx = self.LANDMARKS["RIGHT_ANKLE"]
        else:
            shoulder_idx = self.LANDMARKS["LEFT_SHOULDER"]
            elbow_idx = self.LANDMARKS["LEFT_ELBOW"]
            wrist_idx = self.LANDMARKS["LEFT_WRIST"]
            hip_idx = self.LANDMARKS["LEFT_HIP"]
            knee_idx = self.LANDMARKS["LEFT_KNEE"]
            ankle_idx = self.LANDMARKS["LEFT_ANKLE"]
        
        shoulder = self.get_landmark(landmarks, shoulder_idx)
        elbow = self.get_landmark(landmarks, elbow_idx)
        wrist = self.get_landmark(landmarks, wrist_idx)
        hip = self.get_landmark(landmarks, hip_idx)
        knee = self.get_landmark(landmarks, knee_idx)
        ankle = self.get_landmark(landmarks, ankle_idx)
        
        # Analyze arm extension (shoulder-elbow-wrist angle)
        arm_angle = self.calculate_angle(shoulder, elbow, wrist)
        joint_angles['arm_extension'] = arm_angle
        
        if "Drive" in skill_name or "Topspin" in skill_name:
            # For drive shots, arm should be moderately extended (130-170 degrees)
            if 130 <= arm_angle <= 170:
                feedback.append("✅ Good arm extension.")
            elif arm_angle < 130:
                feedback.append("❌ Elbow too bent - extend more.")
                technique_score -= 15
            else:
                feedback.append("⚠️ Arm too straight - slight bend needed.")
                technique_score -= 10
        
        # Analyze knee flexion
        knee_angle = self.calculate_angle(hip, knee, ankle)
        joint_angles['knee_flexion'] = knee_angle
        
        if 140 <= knee_angle <= 170:
            feedback.append("✅ Good knee bend for stability.")
        elif knee_angle < 140:
            feedback.append("⚠️ Too much knee bend - raise up slightly.")
            technique_score -= 10
        else:
            feedback.append("❌ Insufficient knee bend - lower your stance.")
            technique_score -= 15
        
        # Check elbow height relative to shoulder
        if elbow['y'] > shoulder['y'] + 0.1:
            feedback.append("❌ Elbow too low - keep it up.")
            technique_score -= 15
        
        # Check wrist position (should be slightly higher than elbow for topspin)
        if "Topspin" in skill_name:
            if wrist['y'] < elbow['y']:
                feedback.append("✅ Good wrist position for topspin.")
            else:
                feedback.append("⚠️ Wrist should be higher than elbow for topspin.")
                technique_score -= 10
        
        return {
            "score": max(0, technique_score),
            "technique_accuracy": max(0, technique_score),
            "feedback": feedback,
            "joint_angles": joint_angles
        }
    
    def analyze_boxing(self, landmarks: List[Dict], skill_name: str) -> Dict:
        """Analyze Boxing specific techniques"""
        feedback = []
        joint_angles = {}
        technique_score = 100
        
        # Get key landmarks for both sides
        left_shoulder = self.get_landmark(landmarks, self.LANDMARKS["LEFT_SHOULDER"])
        right_shoulder = self.get_landmark(landmarks, self.LANDMARKS["RIGHT_SHOULDER"])
        left_elbow = self.get_landmark(landmarks, self.LANDMARKS["LEFT_ELBOW"])
        right_elbow = self.get_landmark(landmarks, self.LANDMARKS["RIGHT_ELBOW"])
        left_wrist = self.get_landmark(landmarks, self.LANDMARKS["LEFT_WRIST"])
        right_wrist = self.get_landmark(landmarks, self.LANDMARKS["RIGHT_WRIST"])
        left_hip = self.get_landmark(landmarks, self.LANDMARKS["LEFT_HIP"])
        right_hip = self.get_landmark(landmarks, self.LANDMARKS["RIGHT_HIP"])
        nose = self.get_landmark(landmarks, self.LANDMARKS["NOSE"])
        
        # Analyze guard position
        if "Guard" in skill_name or skill_name == "Guard Position":
            # Both hands should be near face level
            avg_shoulder_y = (left_shoulder['y'] + right_shoulder['y']) / 2
            
            if left_wrist['y'] < avg_shoulder_y and right_wrist['y'] < avg_shoulder_y:
                feedback.append("✅ Good guard position - hands up.")
            else:
                feedback.append("❌ Guard dropped - keep hands up at chin level.")
                technique_score -= 20
            
            # Check elbow position (should be tucked)
            left_elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)
            
            joint_angles['left_elbow'] = left_elbow_angle
            joint_angles['right_elbow'] = right_elbow_angle
            
            if 60 <= left_elbow_angle <= 110 and 60 <= right_elbow_angle <= 110:
                feedback.append("✅ Elbows properly tucked.")
            else:
                feedback.append("⚠️ Tuck elbows closer to body.")
                technique_score -= 10
        
        # Analyze punches
        if skill_name in ["Jab", "Cross"]:
            # Determine which hand is punching
            punching_side = "LEFT" if "Jab" in skill_name else "RIGHT"
            
            if punching_side == "LEFT":
                punch_shoulder = left_shoulder
                punch_elbow = left_elbow
                punch_wrist = left_wrist
                guard_wrist = right_wrist
            else:
                punch_shoulder = right_shoulder
                punch_elbow = right_elbow
                punch_wrist = right_wrist
                guard_wrist = left_wrist
            
            # Check punch extension
            punch_angle = self.calculate_angle(punch_shoulder, punch_elbow, punch_wrist)
            joint_angles['punch_extension'] = punch_angle
            
            if punch_angle > 160:
                feedback.append("✅ Full punch extension.")
            elif punch_angle > 140:
                feedback.append("⚠️ Punch not fully extended.")
                technique_score -= 10
            else:
                feedback.append("❌ Punch too short - extend fully.")
                technique_score -= 20
            
            # Check if guard hand is up
            if guard_wrist['y'] < punch_shoulder['y']:
                feedback.append("✅ Guard hand maintained.")
            else:
                feedback.append("❌ Guard hand dropped - protect your face.")
                technique_score -= 15
            
            # Check hip rotation for Cross
            if "Cross" in skill_name:
                hip_rotation = abs(left_hip['x'] - right_hip['x'])
                if hip_rotation > 0.1:
                    feedback.append("✅ Good hip rotation.")
                else:
                    feedback.append("⚠️ Rotate hips more for power.")
                    technique_score -= 10
        
        # Analyze Hook
        if "Hook" in skill_name:
            # Check for 90-degree elbow bend
            left_elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)
            
            # Determine which side is hooking (lower elbow position)
            if left_wrist['x'] < right_wrist['x']:
                hook_angle = left_elbow_angle
            else:
                hook_angle = right_elbow_angle
            
            joint_angles['hook_elbow'] = hook_angle
            
            if 80 <= hook_angle <= 100:
                feedback.append("✅ Perfect 90-degree elbow for hook.")
            else:
                feedback.append("❌ Maintain 90-degree elbow bend for hook.")
                technique_score -= 15
        
        # Analyze Uppercut
        if "Uppercut" in skill_name:
            # Check for upward motion (wrist should be moving up)
            # This is simplified - in real analysis, we'd track motion over time
            if left_wrist['y'] < left_shoulder['y'] or right_wrist['y'] < right_shoulder['y']:
                feedback.append("✅ Good upward drive.")
            else:
                feedback.append("⚠️ Drive upward more with legs.")
                technique_score -= 10
        
        return {
            "score": max(0, technique_score),
            "technique_accuracy": max(0, technique_score),
            "feedback": feedback,
            "joint_angles": joint_angles
        }
    
    def analyze_frame(self, landmarks: List[Dict], skill_name: str) -> Dict:
        """Main analysis method that routes to sport-specific analyzers"""
        # Analyze balance (common to both sports)
        balance_score, balance_feedback = self.analyze_balance(landmarks)
        
        # Sport-specific analysis
        if self.sport_type == "table_tennis":
            result = self.analyze_table_tennis(landmarks, skill_name)
        elif self.sport_type == "boxing":
            result = self.analyze_boxing(landmarks, skill_name)
        else:
            return {
                "score": 0,
                "technique_accuracy": 0,
                "balance_score": 0,
                "feedback": ["Invalid sport type"],
                "joint_angles": {}
            }
        
        # Add balance feedback
        result["feedback"].append(balance_feedback)
        result["balance_score"] = balance_score
        
        # Calculate overall score
        result["score"] = (result["technique_accuracy"] * 0.7 + balance_score * 0.3)
        
        return result
