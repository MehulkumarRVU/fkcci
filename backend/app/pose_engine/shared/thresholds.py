"""Compatibility shim.

The skill-level tolerance logic that used to live here now lives in
skill_profiles.py (ToleranceProfile per beginner/intermediate/advanced,
covering range width, penalty scaling, and feedback detail together). This
module re-exports the same function names so the sport analyzers that
already import `from ..shared.thresholds import scale_penalty, effective_min,
effective_max, widen_range` keep working unchanged; new code should prefer
importing directly from skill_profiles.
"""
from .confidence import VISIBILITY_THRESHOLD  # noqa: F401 - re-exported for existing imports
from .skill_profiles import (  # noqa: F401
    PROFILES as SKILL_LEVEL_TOLERANCE,
    effective_max,
    effective_min,
    get_profile as get_tolerance_profile,
    scale_penalty,
    widen_range,
)

# Generic balance thresholds - the shared fallback used by
# PoseUtils.analyze_balance for every sport (no per-sport override exists
# today; camera-framing dependence is a known limitation, see PoseUtils docs).
BALANCE_NARROW_RATIO = 0.8
BALANCE_WIDE_RATIO = 2.0
BALANCE_LEVEL_DIFF = 0.05

DEFAULT_TOLERANCE = 1.0


def get_tolerance(skill_level) -> float:
    return get_tolerance_profile(skill_level).range_multiplier
