from typing import Dict, List

from ..pose_engine.analyzer_factory import AnalyzerFactory


class AnalysisService:
    def analyze_frame(self, sport_type: str, skill_name: str, landmarks: List[Dict[str, float]]) -> Dict:
        analyzer = AnalyzerFactory.get_analyzer(sport_type)
        return analyzer.analyze_frame(landmarks, skill_name)

    def analyze_session(self, sport_type: str, skill_name: str, pose_sequence: List[List[Dict[str, float]]]) -> Dict:
        analyzer = AnalyzerFactory.get_analyzer(sport_type)
        return analyzer.analyze_session(pose_sequence, skill_name)
