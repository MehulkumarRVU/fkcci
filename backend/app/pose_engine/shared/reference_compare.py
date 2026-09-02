"""Classifies how far a measured joint angle deviates from its ideal range,
for the ideal-form overlay (Digital Twin part 2).

Reuses the same low/high band each analyzer already checks against via
`BaseAnalyzer.check_range` - not a second parallel threshold table that could
drift out of sync with the scoring logic (the exact bug this whole refactor
was fixing between frontend/backend balance checks).
"""
from typing import Dict, Optional

# How far outside the (skill-level-widened) acceptable band counts as a
# "medium" vs "high" deviation, as a fraction of the band's half-width.
MEDIUM_DEVIATION_FACTOR = 0.5


def classify_deviation(value: Optional[float], low: float, high: float) -> Optional[str]:
    """Returns 'low' (within range - good), 'medium', or 'high' severity.
    Returns None when `value` is None (landmark not confidently visible) -
    there's nothing honest to report."""
    if value is None:
        return None
    if low <= value <= high:
        return "low"

    half_width = max((high - low) / 2.0, 1e-6)
    if value < low:
        overshoot = (low - value) / half_width
    else:
        overshoot = (value - high) / half_width

    return "medium" if overshoot <= MEDIUM_DEVIATION_FACTOR else "high"


def build_landmark_deviations(angle_checks: Dict[int, tuple]) -> Dict[int, str]:
    """angle_checks: {landmark_index: (value, low, high)}. Returns
    {landmark_index: severity} skipping any entry with severity None."""
    deviations = {}
    for landmark_index, (value, low, high) in angle_checks.items():
        severity = classify_deviation(value, low, high)
        if severity is not None:
            deviations[landmark_index] = severity
    return deviations
