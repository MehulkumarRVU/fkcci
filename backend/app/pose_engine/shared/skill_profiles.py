"""Skill-level tolerance profiles.

Each profile controls three independent things for a given athlete
skill_level: how wide a check's acceptable range is, how heavily a failed
check is penalized, and how much feedback detail is surfaced (beginner gets
fundamentals, advanced gets biomechanical detail) - Athlete.skill_level has
always existed in the DB but nothing previously read it.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ToleranceProfile:
    level: str
    range_multiplier: float    # >1 widens acceptable ranges, <1 narrows them
    penalty_multiplier: float  # >1 softens penalties, <1 amplifies them
    feedback_detail: str       # "fundamental" | "technical" | "biomechanical"


PROFILES = {
    "beginner": ToleranceProfile("beginner", range_multiplier=1.4, penalty_multiplier=1.4, feedback_detail="fundamental"),
    "intermediate": ToleranceProfile("intermediate", range_multiplier=1.0, penalty_multiplier=1.0, feedback_detail="technical"),
    "advanced": ToleranceProfile("advanced", range_multiplier=0.7, penalty_multiplier=0.7, feedback_detail="biomechanical"),
}

DEFAULT_LEVEL = "beginner"


def get_profile(skill_level) -> ToleranceProfile:
    if not skill_level:
        return PROFILES[DEFAULT_LEVEL]
    return PROFILES.get(str(skill_level).lower(), PROFILES[DEFAULT_LEVEL])


def widen_range(low: float, high: float, skill_level) -> tuple:
    """Widen [low, high] around its center by the skill-level's range_multiplier."""
    profile = get_profile(skill_level)
    center = (low + high) / 2.0
    half = (high - low) / 2.0 * profile.range_multiplier
    return center - half, center + half


def effective_min(threshold: float, skill_level) -> float:
    profile = get_profile(skill_level)
    return threshold / profile.range_multiplier if profile.range_multiplier else threshold


def effective_max(threshold: float, skill_level) -> float:
    profile = get_profile(skill_level)
    return threshold * profile.range_multiplier


def scale_penalty(penalty: float, skill_level) -> float:
    profile = get_profile(skill_level)
    return penalty / profile.penalty_multiplier if profile.penalty_multiplier else penalty


def feedback_detail(skill_level) -> str:
    return get_profile(skill_level).feedback_detail
