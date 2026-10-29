from typing import Dict, List, Optional

from ..pose_engine.analyzer_factory import AnalyzerFactory


class AnalysisService:
    def analyzer_for(self, sport_type: str):
        return AnalyzerFactory.get_analyzer(sport_type)

    def analyze_frame(self, sport_type: str, skill_name: str, landmarks: List[Dict[str, float]],
                       skill_level: str = "beginner", dominant_hand: str = "right") -> Dict:
        analyzer = self.analyzer_for(sport_type)
        return analyzer.analyze_frame_full(landmarks, skill_name, skill_level, dominant_hand)

    def analyze_session(self, sport_type: str, skill_name: str, pose_sequence: List[List[Dict[str, float]]],
                         skill_level: str = "beginner", dominant_hand: str = "right",
                         timestamps: Optional[List[float]] = None) -> Dict:
        analyzer = self.analyzer_for(sport_type)
        return analyzer.analyze_session(pose_sequence, skill_name, skill_level, dominant_hand, timestamps)
