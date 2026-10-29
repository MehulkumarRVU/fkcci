"""Body-relative landmark normalization for scale-robust feature extraction."""

import math
from typing import Dict, List, Optional


def _point(landmark: Optional[Dict[str, float]]) -> Optional[tuple[float, float, float]]:
    if not landmark:
        return None
    values = tuple(landmark.get(axis) for axis in ("x", "y", "z"))
    if not all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in values):
        return None
    return values  # type: ignore[return-value]


def body_scale(landmarks: List[Dict[str, float]]) -> Optional[float]:
    """Return shoulder-to-hip torso length, or None when the torso is invalid."""
    shoulder = _point({
        "x": (landmarks[11]["x"] + landmarks[12]["x"]) / 2,
        "y": (landmarks[11]["y"] + landmarks[12]["y"]) / 2,
        "z": (landmarks[11]["z"] + landmarks[12]["z"]) / 2,
    }) if len(landmarks) > 12 and landmarks[11] and landmarks[12] else None
    hip = _point({
        "x": (landmarks[23]["x"] + landmarks[24]["x"]) / 2,
        "y": (landmarks[23]["y"] + landmarks[24]["y"]) / 2,
        "z": (landmarks[23]["z"] + landmarks[24]["z"]) / 2,
    }) if len(landmarks) > 24 and landmarks[23] and landmarks[24] else None
    if shoulder is None or hip is None:
        return None
    scale = math.dist(shoulder, hip)
    return scale if scale > 1e-6 else None


def normalize_landmarks(landmarks: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Translate to the mid-hip and scale by torso length.

    Missing or low-quality landmarks are copied unchanged; no coordinates are
    fabricated. The result is intended for feature extraction, not rendering.
    """
    if len(landmarks) <= 24 or not landmarks[23] or not landmarks[24]:
        return [dict(landmark) if landmark else landmark for landmark in landmarks]
    hip_left = _point(landmarks[23])
    hip_right = _point(landmarks[24])
    scale = body_scale(landmarks)
    if hip_left is None or hip_right is None or scale is None:
        return [dict(landmark) if landmark else landmark for landmark in landmarks]
    origin = tuple((hip_left[i] + hip_right[i]) / 2 for i in range(3))
    normalized = []
    for landmark in landmarks:
        point = _point(landmark)
        if point is None:
            normalized.append(dict(landmark) if landmark else landmark)
            continue
        normalized.append({
            "x": (point[0] - origin[0]) / scale,
            "y": (point[1] - origin[1]) / scale,
            "z": (point[2] - origin[2]) / scale,
            "visibility": landmark.get("visibility", 0.0),
        })
    return normalized
