-- Migration: add skill_reference_poses table
-- Documented "ideal form" joint-angle ranges per skill/skill_level, used by
-- the Digital Twin ideal-form overlay feature.
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS skill_reference_poses (
    id INTEGER PRIMARY KEY,
    skill_id INTEGER NOT NULL,
    skill_level VARCHAR NOT NULL DEFAULT 'beginner',
    checkpoint_name VARCHAR NOT NULL DEFAULT 'default',
    joint_angle_ranges TEXT NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY(skill_id) REFERENCES skills(id)
);
COMMIT;
PRAGMA foreign_keys=ON;
