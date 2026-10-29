"""Per-landmark quality gating and aggregate pose-confidence scoring.

This is deliberately separate from technique/balance/performance scoring:
`coverage()` answers "how much do we trust this frame's landmarks at all",
which callers can report as its own field (`pose_confidence`) instead of
silently treating a fully-occluded frame the same as a clearly visible one -
previously nothing in the pose engine checked `visibility` at all.
"""
import math
import os
from typing import Dict, List, Optional

VISIBILITY_THRESHOLD = float(os.getenv("POSE_VISIBILITY_THRESHOLD", "0.5"))
MIN_FRAME_COVERAGE = float(os.getenv("POSE_MIN_FRAME_COVERAGE", "0.5"))
CORE_LANDMARK_INDICES = [11, 12, 23, 24]


class ConfidenceGate:
    def __init__(self, threshold: float = VISIBILITY_THRESHOLD):
        self.threshold = threshold

    def is_confident(self, landmark: Optional[Dict[str, float]]) -> bool:
        if not landmark or landmark.get("visibility", 0.0) < self.threshold:
            return False
        return all(
            isinstance(landmark.get(axis), (int, float))
            and math.isfinite(float(landmark[axis]))
            for axis in ("x", "y", "z")
        )

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

    def frame_quality(self, landmarks: List[Dict[str, float]],
                      min_coverage: float = MIN_FRAME_COVERAGE,
                      required_indices: Optional[List[int]] = None) -> Dict[str, object]:
        """Return an explicit quality decision for downstream evaluation.

        Visibility and coordinate validity are kept separate from technique
        scoring so an occluded or malformed frame cannot be presented as a
        technically poor movement.
        """
        indices = required_indices if required_indices is not None else list(range(len(landmarks)))
        coverage = self.coverage(landmarks, indices)
        core_coverage = self.coverage(landmarks, CORE_LANDMARK_INDICES)
        reasons = []
        if not landmarks:
            reasons.append("no_landmarks")
        elif coverage < min_coverage:
            reasons.append("insufficient_landmark_visibility")
        if required_indices is None and core_coverage < 1.0:
            reasons.append("torso_not_reliably_visible")
        relevant_landmarks = (
            [landmarks[i] for i in required_indices if i < len(landmarks)]
            if required_indices is not None else landmarks
        )
        invalid_count = sum(
            1 for lm in relevant_landmarks
            if lm and not all(
                isinstance(lm.get(axis), (int, float))
                and math.isfinite(float(lm[axis]))
                for axis in ("x", "y", "z")
            )
        )
        if invalid_count:
            reasons.append("invalid_landmark_coordinates")
        return {
            "coverage": coverage,
            "core_coverage": core_coverage,
            "is_reliable": not reasons,
            "reasons": reasons,
        }


DEFAULT_GATE = ConfidenceGate()
