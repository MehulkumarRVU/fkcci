from app.pose_engine.analyzer_factory import AnalyzerFactory, AIGymCoachAnalyzer
from app.sports_registry import (
    ACTIVE_CATEGORIES,
    LEGACY_CATEGORIES,
    get_sport_display_name,
    get_supported_sport_types,
    is_valid_sport,
)


EXPECTED_CATEGORIES = {
    "boxing",
    "table_tennis",
    "gym",
    "badminton",
    "stretching",
    "mobility_training",
    "rehabilitation",
    "home_workouts",
    "calisthenics",
}


def test_public_registry_contains_exactly_nine_active_categories():
    assert set(get_supported_sport_types()) == EXPECTED_CATEGORIES
    assert set(ACTIVE_CATEGORIES) == EXPECTED_CATEGORIES


def test_legacy_categories_are_displayable_but_not_valid_for_new_data():
    assert "ai_gym_coach" in LEGACY_CATEGORIES
    assert not is_valid_sport("ai_gym_coach")
    assert get_sport_display_name("ai_gym_coach") == "AI Gym Coach"


def test_gym_uses_the_gym_analyzer():
    assert isinstance(AnalyzerFactory.get_analyzer("gym"), AIGymCoachAnalyzer)
