"""Seeds documented ideal-form joint-angle references for the Digital Twin
overlay feature. Priority tier (table_tennis, boxing) gets ranges matching
what their analyzers actually check (backend/app/pose_engine/sports/
table_tennis_analyzer.py, boxing_analyzer.py); per-skill-level bands are
derived from the same skill_profiles.widen_range() the live analyzers use,
so the seeded "documented" ranges can't silently drift from the real
scoring logic.

Run directly: python backend/seed_reference_poses.py
"""
from app.database import SessionLocal
from app.models.skill import Skill
from app.models.skill_reference_pose import SkillReferencePose
from app.pose_engine.shared.skill_profiles import widen_range

SKILL_LEVELS = ["beginner", "intermediate", "advanced"]

# skill_name -> {joint_name: (low, high)} base (intermediate-equivalent) range
BASE_RANGES = {
    # Table tennis
    "Forehand Drive": {"arm_extension": (130, 170), "knee_flexion": (140, 170)},
    "Backhand Drive": {"arm_extension": (130, 170), "knee_flexion": (140, 170)},
    "Topspin": {"arm_extension": (130, 170), "knee_flexion": (140, 170)},
    "Smash": {"arm_extension": (130, 170), "knee_flexion": (140, 170)},
    # Boxing
    "Jab": {"punch_extension": (160, 180)},
    "Cross": {"punch_extension": (160, 180)},
    "Hook": {"hook_elbow": (80, 100)},
    "Guard Position": {"elbow_tuck": (60, 110)},
}


def seed_reference_poses_if_empty(db) -> str:
    existing = db.query(SkillReferencePose).first()
    if existing:
        return "Reference poses already seeded, skipping."

    created = 0
    for skill_name, joint_ranges in BASE_RANGES.items():
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if not skill:
            continue

        for level in SKILL_LEVELS:
            level_ranges = {}
            for joint_name, (low, high) in joint_ranges.items():
                adj_low, adj_high = widen_range(low, high, level)
                level_ranges[joint_name] = [round(adj_low, 1), round(adj_high, 1)]

            db.add(SkillReferencePose(
                skill_id=skill.id,
                skill_level=level,
                checkpoint_name="default",
                joint_angle_ranges=level_ranges,
                notes=f"Auto-derived from {skill_name} analyzer thresholds for {level} tolerance.",
            ))
            created += 1

    db.commit()
    return f"Seeded {created} reference pose entries."


if __name__ == "__main__":
    with SessionLocal() as db:
        print(seed_reference_poses_if_empty(db))
