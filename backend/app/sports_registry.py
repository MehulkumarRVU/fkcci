from typing import Dict, List, Optional

SUPPORTED_SPORTS: Dict[str, Dict[str, str]] = {
    "table_tennis": {"name": "Table Tennis", "icon": "🏓"},
    "boxing": {"name": "Boxing", "icon": "🥊"},
    "badminton": {"name": "Badminton", "icon": "🏸"},
    # Racket Sports
    "tennis": {"name": "Tennis", "icon": "🎾"},
    "pickleball": {"name": "Pickleball", "icon": "🥎"},
    "squash": {"name": "Squash", "icon": "🏓"},
    # Combat / Martial Arts
    "kickboxing": {"name": "Kickboxing", "icon": "🥊"},
    "muay_thai": {"name": "Muay Thai", "icon": "🦵"},
    "karate": {"name": "Karate", "icon": "🥋"},
    "taekwondo": {"name": "Taekwondo", "icon": "🥋"},
    "judo": {"name": "Judo", "icon": "🥋"},
    "bjj": {"name": "Brazilian Jiu-Jitsu", "icon": "🥋"},
    "wrestling": {"name": "Wrestling", "icon": "🤼"},
    "fencing": {"name": "Fencing", "icon": "🤺"},
    # Court & Team Sports
    "basketball": {"name": "Basketball", "icon": "🏀"},
    "volleyball": {"name": "Volleyball", "icon": "🏐"},
    "handball": {"name": "Handball", "icon": "🤾"},
    "football": {"name": "Football", "icon": "⚽"},
    # Precision & Fitness
    "indoor_archery": {"name": "Indoor Archery", "icon": "🏹"},
    "ai_gym_coach": {"name": "AI Gym Coach", "icon": "🏋️"},
    "stretching": {"name": "Stretching", "icon": "🤸"},
    "mobility_training": {"name": "Mobility Training", "icon": "🦴"},
    "rehabilitation": {"name": "Rehabilitation", "icon": "🩺"},
    "home_workouts": {"name": "Home Workouts", "icon": "🏠"},
    "calisthenics": {"name": "Calisthenics", "icon": "💪"},
    # Imported archive sports
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

VALID_SPORTS = set(SUPPORTED_SPORTS.keys())


def is_valid_sport(sport_type: str) -> bool:
    return sport_type in VALID_SPORTS


def get_supported_sport_types() -> List[str]:
    return list(SUPPORTED_SPORTS.keys())


def get_sport_display_name(sport_type: str) -> str:
    return SUPPORTED_SPORTS.get(sport_type, {}).get("name", sport_type)


def get_sport_icon(sport_type: str) -> str:
    return SUPPORTED_SPORTS.get(sport_type, {}).get("icon", "🏅")


def get_sport_metadata(sport_type: str) -> Dict[str, str]:
    return SUPPORTED_SPORTS.get(sport_type, {"name": sport_type, "icon": "🏅"})
