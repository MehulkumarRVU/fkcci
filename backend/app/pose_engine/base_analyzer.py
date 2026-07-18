from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAnalyzer(ABC):
    """Base class for all pose analyzers."""

    def __init__(self, sport_type: str):
        self.sport_type = sport_type

    @abstractmethod
    def analyze_frame(self, landmarks: List[Dict[str, float]], skill_name: str) -> Dict[str, Any]:
        """Analyze a single frame of pose landmarks."""
        raise NotImplementedError

    @abstractmethod
    def analyze_session(self, pose_sequence: List[List[Dict[str, float]]], skill_name: str) -> Dict[str, Any]:
        """Analyze a full session of pose landmarks."""
        raise NotImplementedError

    @abstractmethod
    def get_supported_skills(self) -> List[str]:
        """Return supported skill names for this analyzer."""
        raise NotImplementedError
