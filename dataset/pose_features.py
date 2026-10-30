"""Shared MediaPipe landmark feature extraction for training and evaluation."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

LANDMARK_COUNT = 33
REQUIRED_INDICES = (11, 12, 23, 24)
VISIBILITY_THRESHOLD = 0.5
ANGLE_TRIPLETS = (
    (11, 13, 15), (12, 14, 16),
    (23, 25, 27), (24, 26, 28),
    (11, 23, 25), (12, 24, 26),
)
LENGTH_PAIRS = (
    (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 25), (25, 27),
    (24, 26), (26, 28),
)


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    first = a[:2] - b[:2]
    second = c[:2] - b[:2]
    denominator = np.linalg.norm(first) * np.linalg.norm(second)
    if denominator <= 1e-8:
        return float("nan")
    cosine = np.clip(np.dot(first, second) / denominator, -1.0, 1.0)
    return float(math.degrees(math.acos(cosine)) / 180.0)


def extract_feature(landmarks: Any, visibility_threshold: float = VISIBILITY_THRESHOLD) -> np.ndarray:
    """Return a fixed feature vector or raise when required evidence is absent.

    Missing landmarks are never replaced with zero. A sample is rejected if
    required torso points or any feature point are below the visibility gate.
    """
    points = np.array(
        [[lm.x, lm.y, lm.z, lm.visibility] for lm in landmarks.landmark],
        dtype=np.float32,
    )
    if points.shape != (LANDMARK_COUNT, 4):
        raise ValueError("unexpected_landmark_count")
    if any(points[index, 3] < visibility_threshold for index in REQUIRED_INDICES):
        raise ValueError("insufficient_torso_visibility")

    center = (points[11, :3] + points[12, :3]) / 2.0
    scale = float(np.linalg.norm(points[11, :2] - points[12, :2]))
    if scale <= 1e-6:
        raise ValueError("shoulder_width_too_small")
    normalized = (points[:, :3] - center) / scale
    confidence = points[:, 3:4]
    relative = normalized.reshape(-1)
    angles = np.array(
        [_angle(normalized[a], normalized[b], normalized[c]) for a, b, c in ANGLE_TRIPLETS],
        dtype=np.float32,
    )
    lengths = np.array(
        [np.linalg.norm(normalized[a] - normalized[b]) for a, b in LENGTH_PAIRS],
        dtype=np.float32,
    )
    symmetry = np.array(
        [normalized[left, 0] + normalized[right, 0] for left, right in ((11, 12), (13, 14), (15, 16), (23, 24), (25, 26), (27, 28))],
        dtype=np.float32,
    )
    vector = np.concatenate((relative, confidence.reshape(-1), angles, lengths, symmetry))
    if not np.isfinite(vector).all():
        raise ValueError("non_finite_feature")
    return vector.astype(np.float32)
