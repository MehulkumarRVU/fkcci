"""Temporal smoothing for session-level analysis: landmark-level EMA
smoothing + low-confidence frame rejection before per-frame scoring, and
score-level outlier rejection + EMA afterward.

Previously every analyzer's `analyze_session` was a flat arithmetic mean of
independent single-frame scores computed from raw, unsmoothed, unfiltered
landmarks - a single noisy/misdetected frame swung the session score
directly.
"""
import math
from typing import Dict, List, Optional, Tuple

from .confidence import DEFAULT_GATE

EMA_ALPHA = 0.3
OUTLIER_STD_MULTIPLIER = 2.5
MIN_FRAME_COVERAGE = 0.4


def reject_low_confidence_frames(
    pose_sequence: List[List[Dict[str, float]]], timestamps: Optional[List[float]] = None,
    min_coverage: float = MIN_FRAME_COVERAGE
) -> Tuple[List[List[Dict[str, float]]], Optional[List[float]]]:
    """Drop frames whose landmark coverage is too low to trust (e.g. athlete
    briefly stepped out of frame), keeping any timestamps aligned."""
    kept_frames = []
    kept_timestamps = [] if timestamps is not None else None
    for i, frame in enumerate(pose_sequence):
        if DEFAULT_GATE.coverage(frame) >= min_coverage:
            kept_frames.append(frame)
            if kept_timestamps is not None:
                kept_timestamps.append(timestamps[i])
    return kept_frames, kept_timestamps


def smooth_landmarks(pose_sequence: List[List[Dict[str, float]]], alpha: float = 0.4) -> List[List[Dict[str, float]]]:
    """EMA-smooth each landmark's x/y/z across a pose sequence to reduce
    per-frame jitter before running per-frame/session-level analysis on it."""
    if not pose_sequence:
        return pose_sequence

    smoothed = [pose_sequence[0]]
    prev = pose_sequence[0]
    for frame in pose_sequence[1:]:
        new_frame = []
        for i, lm in enumerate(frame):
            if not lm:
                new_frame.append(lm)
                continue
            coordinates_valid = all(
                isinstance(lm.get(axis), (int, float))
                and math.isfinite(float(lm[axis]))
                for axis in ("x", "y", "z")
            )
            # Never turn an occluded/malformed landmark into a fabricated
            # previous position. Invalid points remain invalid and are
            # excluded by the confidence gate during scoring.
            if lm.get("visibility", 0.0) < DEFAULT_GATE.threshold or not coordinates_valid:
                new_frame.append(dict(lm))
                continue
            prev_lm = prev[i] if i < len(prev) else lm
            prev_valid = all(
                isinstance(prev_lm.get(axis), (int, float))
                and math.isfinite(float(prev_lm[axis]))
                for axis in ("x", "y", "z")
            )
            if not prev_valid:
                new_frame.append(dict(lm))
                continue
            new_frame.append({
                "x": alpha * lm["x"] + (1 - alpha) * prev_lm["x"],
                "y": alpha * lm["y"] + (1 - alpha) * prev_lm["y"],
                "z": alpha * lm["z"] + (1 - alpha) * prev_lm["z"],
                # visibility is a detector confidence signal, not a position -
                # smoothing it would mask genuine occlusion, so pass it through.
                "visibility": lm.get("visibility", 0.0),
            })
        smoothed.append(new_frame)
        prev = new_frame
    return smoothed


def smooth_series(values: List[float]) -> List[float]:
    """Reject statistical outliers, then apply an EMA over a score sequence."""
    if len(values) < 3:
        return list(values)

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5

    if std > 0:
        cleaned = [v for v in values if abs(v - mean) <= OUTLIER_STD_MULTIPLIER * std]
        if not cleaned:
            cleaned = values
    else:
        cleaned = values

    smoothed = []
    ema = cleaned[0]
    for v in cleaned:
        ema = EMA_ALPHA * v + (1 - EMA_ALPHA) * ema
        smoothed.append(ema)
    return smoothed
