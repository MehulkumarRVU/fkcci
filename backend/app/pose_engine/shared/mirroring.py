"""Resolves joints generically by the athlete's `dominant_hand` instead of
each analyzer hardcoding the right (or left) side.

This was a real mirroring bug: table_tennis, boxing, badminton, and racket
analyzers all unconditionally used RIGHT_SHOULDER/ELBOW/WRIST regardless of
Athlete.dominant_hand, so a left-handed athlete's dominant-arm technique
(the whole point of the analysis) was scored using their non-dominant arm.
"""
from typing import Dict, List, NamedTuple, Optional, Tuple

from .utils import PoseUtils


class SideLandmarks(NamedTuple):
    shoulder: Dict[str, float]
    elbow: Dict[str, float]
    wrist: Dict[str, float]
    hip: Dict[str, float]
    knee: Dict[str, float]
    ankle: Dict[str, float]


def _side_landmarks(landmarks: List[Dict[str, float]], side: str) -> SideLandmarks:
    prefix = "LEFT" if side == "left" else "RIGHT"
    L = PoseUtils.LANDMARKS
    return SideLandmarks(
        shoulder=PoseUtils.get_landmark(landmarks, L[f"{prefix}_SHOULDER"]),
        elbow=PoseUtils.get_landmark(landmarks, L[f"{prefix}_ELBOW"]),
        wrist=PoseUtils.get_landmark(landmarks, L[f"{prefix}_WRIST"]),
        hip=PoseUtils.get_landmark(landmarks, L[f"{prefix}_HIP"]),
        knee=PoseUtils.get_landmark(landmarks, L[f"{prefix}_KNEE"]),
        ankle=PoseUtils.get_landmark(landmarks, L[f"{prefix}_ANKLE"]),
    )


def normalize_hand(dominant_hand: Optional[str]) -> str:
    side = (dominant_hand or "right").strip().lower()
    return side if side in ("left", "right") else "right"


def get_dominant_and_off_side(
    landmarks: List[Dict[str, float]], dominant_hand: Optional[str]
) -> Tuple[SideLandmarks, SideLandmarks, str]:
    """Returns (dominant_side_landmarks, off_side_landmarks, dominant_side_label)
    resolved from the athlete's recorded dominant_hand, defaulting to 'right'
    only when unknown - not as a silent blanket assumption baked into every
    analyzer."""
    side = normalize_hand(dominant_hand)
    dominant = _side_landmarks(landmarks, side)
    off = _side_landmarks(landmarks, "left" if side == "right" else "right")
    return dominant, off, side


def boxing_stance_sides(dominant_hand: Optional[str]) -> Tuple[str, str]:
    """Orthodox stance (right-handed boxer) leads with the LEFT hand (jab)
    and powers with the RIGHT (cross); southpaw (left-handed) is mirrored -
    leads with RIGHT, powers with LEFT. Returns (lead_side, rear_power_side)."""
    side = normalize_hand(dominant_hand)
    if side == "left":
        return "right", "left"  # southpaw: lead right, power left
    return "left", "right"  # orthodox: lead left, power right
