"""Generic ready-state -> triggered-state reaction timing over a sequence of
per-frame technique scores and their timestamps.

Returns `(None, "insufficient_data" | "not_measured")` rather than
fabricating a number when there isn't a real signal to measure - this
replaces the old frontend fabrication `reaction_score = avg_score * 0.9`
(a fixed multiplier of an unrelated number, not an independent measurement).
"""
from typing import List, Optional, Tuple

READY_THRESHOLD = 85.0      # technique_accuracy at/above this = "ready" (good) state
TRIGGERED_THRESHOLD = 70.0  # technique_accuracy below this = a "triggered" fault event
MIN_FRAMES = 3


def measure_state_transition_reaction(
    technique_scores: List[float], timestamps: Optional[List[float]] = None
) -> Tuple[Optional[float], str]:
    """Finds ready(>=READY_THRESHOLD) -> triggered(<TRIGGERED_THRESHOLD) ->
    recovered(>=READY_THRESHOLD) cycles and measures the triggered->recovered
    gap, in seconds if timestamps are given, otherwise in frames. Returns
    (reaction_score 0-100, "measured") when at least one full cycle is
    observed, or (None, status) when there isn't enough data to measure
    honestly rather than guessing."""
    if len(technique_scores) < MIN_FRAMES:
        return None, "insufficient_data"

    use_timestamps = bool(timestamps) and len(timestamps) == len(technique_scores)

    gaps = []
    state = "ready"
    trigger_index = None
    for i, score in enumerate(technique_scores):
        if state == "ready" and score < TRIGGERED_THRESHOLD:
            state = "triggered"
            trigger_index = i
        elif state == "triggered" and score >= READY_THRESHOLD:
            gap = (timestamps[i] - timestamps[trigger_index]) if use_timestamps else (i - trigger_index)
            gaps.append(gap)
            state = "ready"

    if not gaps:
        # Either no faults ever happened (nothing to time) or a fault never
        # recovered within the session - both are legitimately "not measured"
        # rather than a number we can honestly report.
        return None, "not_measured"

    avg_gap = sum(gaps) / len(gaps)
    scale = 1.5 if use_timestamps else 5.0  # seconds vs. frames
    score = 100.0 * (scale / (scale + avg_gap))
    return max(0.0, min(100.0, score)), "measured"
