from backend.app.database import SessionLocal
from backend.app.seed_data import get_default_skill_data
from backend.app.models.skill import Skill


def test_gym_skill_seed_includes_kaggle_style_exercises():
    skills = get_default_skill_data()
    gym_skills = [skill for skill in skills if skill["sport_type"] == "gym"]

    assert gym_skills, "Expected gym skills to be seeded"
    skill_names = {skill["name"] for skill in gym_skills}

    assert any("Squat" in name for name in skill_names)
    assert any("Push-Up" in name for name in skill_names)
    assert any("Deadlift" in name for name in skill_names)
    assert "Bent-Over Row" in skill_names
    assert "Shoulder Press" in skill_names
    assert "Burpee" in skill_names
    assert "Pull-Up Form" in skill_names
    assert "Dips Technique" in skill_names
    assert "Mountain Climbers" in skill_names
    assert "Bench Press" in skill_names
    assert "Incline Bench Press" in skill_names
    assert "Decline Bench Press" in skill_names
    assert "Tricep Pushdown" in skill_names
    assert "Lat Pulldown" in skill_names
    assert "Barbell Biceps Curl" in skill_names
    assert "Hammer Curl" in skill_names
    assert "T-Bar Row" in skill_names
    assert "Chest Fly Machine" in skill_names
    assert "Romanian Deadlift" in skill_names
    assert "Hip Thrust" in skill_names
    assert "Leg Extension" in skill_names
    assert "Leg Raises" in skill_names
    assert "Plank" in skill_names
    assert "Russian Twist" in skill_names
