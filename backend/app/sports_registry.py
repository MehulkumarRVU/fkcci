"""Canonical training-category registry.

Only ACTIVE_CATEGORIES are selectable for new accounts, skills, sessions, and
analysis requests. LEGACY_CATEGORIES remain readable as metadata for
historical rows and are intentionally excluded from validation.
"""
from typing import Dict, List

ACTIVE_CATEGORIES: Dict[str, Dict[str, str]] = {
    "boxing": {"name": "Boxing", "icon": "🥊"},
    "table_tennis": {"name": "Table Tennis", "icon": "🏓"},
    "gym": {"name": "Gym", "icon": "🏋️"},
    "badminton": {"name": "Badminton", "icon": "🏸"},
    "stretching": {"name": "Stretching", "icon": "🤸"},
    "mobility_training": {"name": "Mobility Training", "icon": "🦴"},
    "rehabilitation": {"name": "Rehabilitation", "icon": "🩺"},
    "home_workouts": {"name": "Home Workouts", "icon": "🏠"},
    "calisthenics": {"name": "Calisthenics", "icon": "💪"},
}

# Historical values remain displayable but cannot be selected or written to
# through current validation paths.
LEGACY_CATEGORIES: Dict[str, Dict[str, str]] = {
    "ai_gym_coach": {"name": "AI Gym Coach", "icon": "🏋️"},
    "tennis": {"name": "Tennis", "icon": "🎾"},
    "pickleball": {"name": "Pickleball", "icon": "🥎"},
    "squash": {"name": "Squash", "icon": "🏓"},
    "kickboxing": {"name": "Kickboxing", "icon": "🥊"},
    "muay_thai": {"name": "Muay Thai", "icon": "🦵"},
    "karate": {"name": "Karate", "icon": "🥋"},
    "taekwondo": {"name": "Taekwondo", "icon": "🥋"},
    "judo": {"name": "Judo", "icon": "🥋"},
    "bjj": {"name": "Brazilian Jiu-Jitsu", "icon": "🥋"},
    "wrestling": {"name": "Wrestling", "icon": "🤼"},
    "fencing": {"name": "Fencing", "icon": "🤺"},
    "basketball": {"name": "Basketball", "icon": "🏀"},
    "volleyball": {"name": "Volleyball", "icon": "🏐"},
    "handball": {"name": "Handball", "icon": "🤾"},
    "football": {"name": "Football", "icon": "⚽"},
    "indoor_archery": {"name": "Indoor Archery", "icon": "🏹"},
    "baseball": {"name": "Baseball", "icon": "⚾"},
    "cricket": {"name": "Cricket", "icon": "🏏"},
    "formula1": {"name": "Formula 1", "icon": "🏎️"},
    "gymnastics": {"name": "Gymnastics", "icon": "🤸"},
    "hockey": {"name": "Hockey", "icon": "🏒"},
    "ice_hockey": {"name": "Ice Hockey", "icon": "🏒"},
    "kabaddi": {"name": "Kabaddi", "icon": "🏅"},
    "motogp": {"name": "MotoGP", "icon": "🏍️"},
    "shooting": {"name": "Shooting", "icon": "🎯"},
    "swimming": {"name": "Swimming", "icon": "🏊"},
    "weight_lifting": {"name": "Weight Lifting", "icon": "🏋️"},
    "wwe": {"name": "WWE", "icon": "🤼"},
}

SUPPORTED_SPORTS = ACTIVE_CATEGORIES
VALID_SPORTS = set(ACTIVE_CATEGORIES)


def is_valid_sport(sport_type: str) -> bool:
    return sport_type in VALID_SPORTS


def get_supported_sport_types() -> List[str]:
    return list(ACTIVE_CATEGORIES)


def get_sport_display_name(sport_type: str) -> str:
    metadata = ACTIVE_CATEGORIES.get(sport_type) or LEGACY_CATEGORIES.get(sport_type)
    return metadata["name"] if metadata else sport_type


def get_sport_icon(sport_type: str) -> str:
    metadata = ACTIVE_CATEGORIES.get(sport_type) or LEGACY_CATEGORIES.get(sport_type)
    return metadata["icon"] if metadata else "🏅"


def get_sport_metadata(sport_type: str) -> Dict[str, str]:
    return ACTIVE_CATEGORIES.get(sport_type) or LEGACY_CATEGORIES.get(
        sport_type, {"name": sport_type, "icon": "🏅"}
    )
