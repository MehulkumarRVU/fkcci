"""Per-landmark visibility gating and aggregate pose-confidence scoring.

This is deliberately separate from technique/balance/performance scoring:
`coverage()` answers "how much do we trust this frame's landmarks at all",
which callers can report as its own field (`pose_confidence`) instead of
silently treating a fully-occluded frame the same as a clearly visible one -
previously nothing in the pose engine checked `visibility` at all.
"""
from typing import Dict, List, Optional

VISIBILITY_THRESHOLD = 0.5


class ConfidenceGate:
    def __init__(self, threshold: float = VISIBILITY_THRESHOLD):
        self.threshold = threshold

    def is_confident(self, landmark: Optional[Dict[str, float]]) -> bool:
        return bool(landmark) and landmark.get("visibility", 0.0) >= self.threshold

    def all_confident(self, *landmarks: Dict[str, float]) -> bool:
        return all(self.is_confident(lm) for lm in landmarks)

    def coverage(self, landmarks: List[Dict[str, float]], indices: Optional[List[int]] = None) -> float:
        """Fraction of the given landmark indices (or all landmarks in the
        frame) that are confidently visible - an aggregate pose-confidence
        score for the frame."""
        if not landmarks:
            return 0.0
        subset = landmarks if indices is None else [landmarks[i] for i in indices if i < len(landmarks)]
        if not subset:
            return 0.0
        confident = sum(1 for lm in subset if self.is_confident(lm))
        return confident / len(subset)


DEFAULT_GATE = ConfidenceGate()
